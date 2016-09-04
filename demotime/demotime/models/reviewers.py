from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from demotime.models.base import BaseModel
from demotime.constants import (
    REVIEWING,
    APPROVED,
    REJECTED
)
from demotime.models import Event, EventType, Message, Reminder


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

    def __str__(self):
        return '{} Follower on {}'.format(
            self.reviewer_display_name,
            self.review.title,
        )

    def to_json(self):
        return {
            'name': self.reviewer.userprofile.name,
            'user_pk': self.reviewer.pk,
            'reviewer_pk': self.pk,
            'reviewer_status': self.status,
            'review_pk': self.review.pk,
        }

    @property
    def reviewer_display_name(self):
        return self.reviewer.userprofile.display_name or self.reviewer.username

    @classmethod
    def create_reviewer(cls, review, reviewer, creator, skip_notifications=False):
        obj = cls.objects.create(
            review=review,
            reviewer=reviewer,
            status=REVIEWING
        )
        Event.create_event(
            project=review.project,
            event_type_code=EventType.REVIEWER_ADDED,
            related_object=obj,
            user=creator
        )
        if skip_notifications:
            notify_reviewer = notify_creator = False
        else:
            notify_reviewer = creator != reviewer
            notify_creator = creator != review.creator
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

        return obj

    def _send_reviewer_message(self, deleted=False, notify_reviewer=False, notify_creator=False):
        if deleted:
            title = 'Deleted as reviewer on: {}'.format(self.review.title)
            receipient = self.reviewer
        elif notify_reviewer:
            title = 'You have been added as a reviewer on: {}'.format(
                self.review.title
            )
            receipient = self.reviewer
        elif notify_creator:
            title = '{} has been added as a reviewer on: {}'.format(
                self.reviewer_display_name,
                self.review.title
            )
            receipient = self.review.creator
        else:
            raise Exception('No receipient for message in reviewer message')

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
        all_statuses = self.review.reviewer_set.values_list('status', flat=True)
        consensus = all(x == APPROVED for x in all_statuses) or all(
            x == REJECTED for x in all_statuses)
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
                'creator': self.review.creator,
                'url': self.review.get_absolute_url(),
                'title': self.review.title,
            }
            Message.send_system_message(
                title,
                'demotime/messages/reviewer_status_change.html',
                context,
                self.review.creator,
                revision=self.review.revision
            )
        return self.review.update_reviewer_state()

    def drop_reviewer(self, dropper):  # pylint: disable=unused-argument
        self._send_reviewer_message(deleted=True)
        Event.create_event(
            project=self.review.project,
            event_type_code=EventType.REVIEWER_REMOVED,
            related_object=self.review,
            user=self.reviewer
        )
        review = self.review
        self.delete()
        review.update_reviewer_state()
