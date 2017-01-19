from datetime import datetime

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from demotime.models.base import BaseModel
from demotime.constants import (
    REVIEWING,
    APPROVED,
    REJECTED
)
from demotime.models import (
    Event, EventType, Message,
    Reminder
)


class ReviewerManager(models.Manager):

    def active(self):
        return self.filter(is_active=True)


class Reviewer(BaseModel):

    STATUS_CHOICES = (
        (REVIEWING, REVIEWING.capitalize()),
        (REJECTED, REJECTED.capitalize()),
        (APPROVED, APPROVED.capitalize())
    )

    review = models.ForeignKey('Review')
    reviewer = models.ForeignKey('auth.User')
    status = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default='reviewing', db_index=True
    )
    events = GenericRelation('Event')
    last_viewed = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    objects = ReviewerManager()

    def __str__(self):
        return '{} Reviewer on {}'.format(
            self.reviewer_display_name,
            self.review.title,
        )

    def to_json(self):
        return {
            'name': self.reviewer.userprofile.name,
            'user_pk': self.reviewer.pk,
            'user_profile_url': self.reviewer.userprofile.get_absolute_url(),
            'reviewer_pk': self.pk,
            'reviewer_status': self.status,
            'review_pk': self.review.pk,
            'is_active': self.is_active,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    @property
    def reviewer_display_name(self):
        return self.reviewer.userprofile.display_name or self.reviewer.username

    def create_reviewer_event(self, user):
        Event.create_event(
            project=self.review.project,
            event_type_code=EventType.REVIEWER_ADDED,
            related_object=self,
            user=user
        )

    @classmethod
    def create_reviewer(cls, review, reviewer, creator,
                        skip_notifications=False, draft=False):
        obj, _ = cls.objects.get_or_create(
            review=review,
            reviewer=reviewer,
            status=REVIEWING
        )
        obj.is_active = True
        obj.save()
        if not draft:
            obj.create_reviewer_event(creator)
            reminder = Reminder.objects.filter(
                user=obj.reviewer,
                review=review,
                reminder_type=Reminder.REVIEWER
            )
            if reminder.exists():
                reminder = reminder.get()
                Reminder.set_activity(review, obj.reviewer, active=True)
            else:
                Reminder.create_reminder(
                    review, obj.reviewer, Reminder.REVIEWER
                )

            if skip_notifications:
                notify_reviewer = notify_creator = False
            else:
                notify_reviewer = creator != reviewer
                notify_creator = not review.creator_set.active().filter(
                    user=creator
                ).exists()
            if notify_reviewer:
                # pylint: disable=protected-access
                obj._send_reviewer_message(
                    notify_reviewer=True, notify_creator=False
                )

            if notify_creator:
                # pylint: disable=protected-access
                obj._send_reviewer_message(
                    notify_reviewer=False, notify_creator=True
                )

            review.update_reviewer_state()
        return obj

    def _send_reviewer_message(self, deleted=False, notify_reviewer=False, notify_creator=False):
        if deleted:
            title = 'Deleted as reviewer on: {}'.format(self.review.title)
            receipients = [self.reviewer]
        elif notify_reviewer:
            title = 'You have been added as a reviewer on: {}'.format(
                self.review.title
            )
            receipients = [self.reviewer]
        elif notify_creator:
            title = '{} has been added as a reviewer on: {}'.format(
                self.reviewer_display_name,
                self.review.title
            )
            receipients = [
                creator.user for creator in self.review.creator_set.active()
            ]
        else:
            raise Exception('No receipient for message in reviewer message')

        for receipient in receipients:
            context = {
                'receipient': receipient,
                'url': self.review.get_absolute_url(),
                'title': self.review.title,
                'deleted': deleted,
                'creator': notify_creator,
                'reviewer': self,
            }
            Message.send_system_message(
                title,
                'demotime/messages/reviewer.html',
                context,
                receipient,
                revision=self.review.revision,
            )

    def set_status(self, status):
        old_status = self.status
        self.status = status
        self.save(update_fields=['status', 'modified'])

        reminder_active = status == REVIEWING
        Reminder.set_activity(self.review, self.reviewer, reminder_active)

        if status == APPROVED:
            event_code = EventType.REVIEWER_APPROVED
        elif status == REJECTED:
            event_code = EventType.REVIEWER_REJECTED
        else:
            event_code = EventType.REVIEWER_RESET
        Event.create_event(
            project=self.review.project,
            event_type_code=event_code,
            related_object=self,
            user=self.reviewer
        )

        # Send a message if this isn't the last person to approve/reject
        consensus, state = self.review.update_reviewer_state()
        if status != old_status and not consensus:
            status_display = '{} {}'.format(
                'resumed' if status == REVIEWING else 'has',
                self.status,
            )
            title = '{} {} your review: {}'.format(
                self.reviewer_display_name,
                status_display,
                self.review.title
            )
            context = {
                'reviewer': self,
                'url': self.review.get_absolute_url(),
                'title': self.review.title,
            }
            for creator in self.review.creator_set.active():
                Message.send_system_message(
                    title,
                    'demotime/messages/reviewer_status_change.html',
                    context,
                    creator.user,
                    revision=self.review.revision
                )
        return consensus, state

    def drop_reviewer(self, dropper, draft=False):  # pylint: disable=unused-argument
        review = self.review
        if draft:
            self.delete()
        else:
            self._send_reviewer_message(deleted=True)
            Event.create_event(
                project=self.review.project,
                event_type_code=EventType.REVIEWER_REMOVED,
                related_object=self,
                user=dropper
            )
        review = self.review
        self.is_active = False
        self.status = REVIEWING
        Reminder.objects.filter(
            review=self.review,
            user=self.reviewer
        ).delete()
        self.save()
        review.update_reviewer_state()

    def viewed_review(self):
        self.last_viewed = datetime.now()
        self.save(update_fields=['last_viewed', 'modified'])
