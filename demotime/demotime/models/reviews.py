from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User

from .attachments import Attachment
from .base import BaseModel
from .messages import Message
from .users import UserReviewStatus
from .reminders import Reminder
from .followers import Follower
from .reviewers import Reviewer

from demotime.constants import (
    REVIEWING,
    REJECTED,
    APPROVED,
    OPEN,
    CLOSED,
    ABORTED
)


class Review(BaseModel):

    STATUS_CHOICES = (
        (OPEN, OPEN.capitalize()),
        (CLOSED, CLOSED.capitalize()),
        (ABORTED, ABORTED.capitalize()),
    )

    REVIEWER_STATE_CHOICES = (
        (REVIEWING, REVIEWING.capitalize()),
        (APPROVED, APPROVED.capitalize()),
        (REJECTED, REJECTED.capitalize()),
    )

    creator = models.ForeignKey('auth.User', related_name='creator')
    reviewers = models.ManyToManyField(
        'auth.User',
        related_name='reviewers',
        through='Reviewer'
    )
    followers = models.ManyToManyField(
        'auth.User',
        related_name='followers',
        through='Follower'
    )
    title = models.CharField(max_length=1024)
    description = models.TextField()
    case_link = models.CharField('Case URL', max_length=2048, blank=True)
    state = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default=OPEN, db_index=True
    )
    reviewer_state = models.CharField(
        max_length=128, choices=REVIEWER_STATE_CHOICES,
        default=REVIEWING, db_index=True
    )
    is_public = models.BooleanField(default=False)
    project = models.ForeignKey('Project')

    def __str__(self):
        return 'Review: {} by {}'.format(
            self.title, self.creator.username
        )

    def get_absolute_url(self):
        return self.revision.get_absolute_url()

    def _send_revision_messages(self, update=False):
        title = 'New Review: {}'.format(self.title)
        if update:
            title = 'Update on Review: {}'.format(self.title)

        for reviewer in self.reviewers.all():
            context = {
                'receipient': reviewer,
                'url': self.get_absolute_url(),
                'update': update,
                'title': self.title,
            }
            Message.send_system_message(
                title,
                'demotime/messages/review.html',
                context,
                reviewer,
                revision=self.revision,
            )

        for follower in self.follower_set.all():
            context = {
                'receipient': follower.user,
                'url': self.get_absolute_url(),
                'update': update,
                'title': self.title,
                'is_follower': True,
            }
            Message.send_system_message(
                title,
                'demotime/messages/review.html',
                context,
                follower.user,
                revision=self.revision,
            )

    @classmethod
    def create_review(
            cls, creator, title, description,
            case_link, reviewers, project,
            followers=None, attachments=None):
        ''' Standard review creation method '''
        obj = cls.objects.create(
            creator=creator,
            title=title,
            description=description,
            case_link=case_link,
            state=OPEN,
            reviewer_state=REVIEWING,
            project=project,
        )
        rev = ReviewRevision.objects.create(
            review=obj,
            description=obj.description,
            number=1,
        )
        for attachment in attachments:
            Attachment.objects.create(
                attachment=attachment['attachment'],
                attachment_type=attachment['attachment_type'],
                description=attachment['description'],
                content_object=rev,
            )
        for reviewer in reviewers:
            Reviewer.create_reviewer(obj, reviewer)
            UserReviewStatus.create_user_review_status(
                obj, reviewer
            )

        for follower in followers:
            Follower.create_follower(obj, follower)
            UserReviewStatus.create_user_review_status(
                obj, follower
            )

        # Creator UserReviewStatus, set read to True, cuz they just created it
        # so I'm assuming they read it
        UserReviewStatus.create_user_review_status(
            obj, obj.creator, True
        )

        # Messages
        obj._send_revision_messages()

        # Reminders
        Reminder.create_reminders_for_review(obj)

        return obj

    @classmethod
    def update_review(
            cls, review, creator, title, description,
            case_link, reviewers, project,
            followers=None, attachments=None
            ):
        ''' Standard update review method '''
        obj = cls.objects.get(pk=review)
        obj.title = title
        obj.case_link = case_link
        obj.project = project
        obj.save()
        prev_revision = obj.revision
        rev_count = obj.reviewrevision_set.count()
        rev = ReviewRevision.objects.create(
            review=obj,
            description=description,
            number=rev_count + 1
        )
        for attachment in attachments:
            Attachment.objects.create(
                attachment=attachment['attachment'],
                attachment_type=attachment['attachment_type'],
                description=attachment['description'],
                content_object=rev,
            )

        # No attachments, we'll copy them over
        if not attachments:
            for attachment in prev_revision.attachments.all():
                attachment.content_object = rev
                attachment.pk = None
                attachment.save()

        for reviewer in reviewers:
            try:
                reviewer = Reviewer.objects.get(review=obj, reviewer=reviewer)
            except Reviewer.DoesNotExist:
                reviewer = Reviewer.create_reviewer(obj, reviewer)
            else:
                reviewer.status = REVIEWING
                reviewer.save()

        for follower in followers:
            try:
                Follower.objects.get(review=obj, user=follower)
            except Follower.DoesNotExist:
                Follower.create_follower(review=obj, user=follower)

        # Update UserReviewStatuses
        UserReviewStatus.objects.filter(review=obj).exclude(
            user=creator
        ).update(read=False)

        # Drop Reviewers no longer assigned
        obj.reviewer_set.exclude(review=obj, reviewer__in=reviewers).delete()
        obj.follower_set.exclude(review=obj, user__in=followers).delete()

        # Messages
        obj._send_revision_messages(update=True)

        # Reminders
        Reminder.update_reminders_for_review(obj)

        return obj

    def _change_reviewer_state(self, state):
        previous_state = self.get_reviewer_state_display()
        self.reviewer_state = state
        self.save(update_fields=['reviewer_state'])
        UserReviewStatus.objects.filter(review=self, user=self.creator).update(
            read=False
        )
        if state == APPROVED:
            Message.send_system_message(
                '"{}" has been Approved!'.format(self.title),
                'demotime/messages/approved.html',
                {'review': self},
                self.creator,
                revision=self.revision,
            )
        elif state == REJECTED:
            Message.send_system_message(
                '"{}" has been Rejected'.format(self.title),
                'demotime/messages/rejected.html',
                {'review': self},
                self.creator,
                revision=self.revision,
            )
        elif state == REVIEWING:
            Message.send_system_message(
                '"{}" is back Under Review'.format(self.title),
                'demotime/messages/reviewing.html',
                {'review': self, 'previous_state': previous_state},
                self.creator,
                revision=self.revision,
            )
        else:
            # Uhh, how'd we get here, eh?
            1/0
            pass

    def update_reviewer_state(self):
        statuses = self.reviewer_set.values_list('status', flat=True)
        approved = all(status == APPROVED for status in statuses)
        rejected = all(status == REJECTED for status in statuses)
        reviewing = not approved and not rejected
        if approved and self.reviewer_state != APPROVED:
            self._change_reviewer_state(APPROVED)
            return True, APPROVED
        elif rejected and self.reviewer_state != REJECTED:
            self._change_reviewer_state(REJECTED)
            return True, REJECTED
        elif reviewing and self.reviewer_state != REVIEWING:
            self._change_reviewer_state(REVIEWING)
            return True, REVIEWING

        return False, ''

    def _reopen_review(self, state):
        # We take a state because this can be closed or aborted, it's okay
        # we don't judge
        prev_state = self.get_state_display()
        self.state = state
        self.save(update_fields=['state'])
        users = User.objects.filter(
            models.Q(reviewer__review=self) | models.Q(follower__review=self),
        ).distinct()
        for user in users:
            Message.send_system_message(
                '"{}" has been Reopened'.format(self.title),
                'demotime/messages/reopened.html',
                {'review': self, 'previous_state': prev_state, 'reviewer': user},
                user,
                revision=self.revision,
            )

        Reminder.update_reminder_activity_for_review(self, True)

        return True

    def _close_review(self, state):
        # We take a state because this can be closed or aborted, it's okay
        # we don't judge
        prev_state = self.get_state_display()
        self.state = state
        self.save(update_fields=['state'])
        users = User.objects.filter(
            models.Q(reviewer__review=self) | models.Q(follower__review=self),
        ).distinct()
        for user in users:
            Message.send_system_message(
                '"{}" has been {}'.format(self.title, state.capitalize()),
                'demotime/messages/closed.html',
                {'review': self, 'previous_state': prev_state, 'reviewer': user},
                user,
                revision=self.revision,
            )

        Reminder.update_reminder_activity_for_review(self)

        return True

    def _common_state_change(self, state):
        ''' General purpose state change things '''
        UserReviewStatus.objects.filter(
            review=self
        ).exclude(user=self.creator).update(
            read=False
        )

    def update_state(self, new_state):
        state_changed = False
        if self.state == OPEN and new_state == CLOSED:
            state_changed = self._close_review(new_state)
        elif self.state == OPEN and new_state == ABORTED:
            state_changed = self._close_review(new_state)
        elif self.state == CLOSED and new_state == OPEN:
            state_changed = self._reopen_review(new_state)
        elif self.state == ABORTED and new_state == OPEN:
            state_changed = self._reopen_review(new_state)

        if state_changed:
            self._common_state_change(new_state)

        return state_changed

    @property
    def revision(self):
        return self.reviewrevision_set.latest()

    @property
    def reviewing_count(self):
        return self.reviewer_set.filter(status=REVIEWING).count()

    @property
    def approved_count(self):
        return self.reviewer_set.filter(status=APPROVED).count()

    @property
    def rejected_count(self):
        return self.reviewer_set.filter(status=REJECTED).count()


class ReviewRevision(BaseModel):

    review = models.ForeignKey('Review')
    description = models.TextField(blank=True)
    attachments = GenericRelation(Attachment)
    number = models.IntegerField()

    def __str__(self):
        return 'Review Revision: {}'.format(self.review)

    def get_absolute_url(self):
        return reverse('review-rev-detail', kwargs={
            'proj_slug': self.review.project.slug,
            'pk': self.review.pk,
            'rev_num': self.number,
        })

    @property
    def is_max_revision(self):
        return self.number == self.review.reviewrevision_set.aggregate(
            Max('number')
        )['number__max']

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']
