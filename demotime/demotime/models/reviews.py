from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User

from demotime.models.base import BaseModel
from demotime.models import (
    Attachment,
    Event,
    EventType,
    Follower,
    Message,
    Reminder,
    Reviewer,
    UserReviewStatus,
)

from demotime import tasks
from demotime.constants import (
    REVIEWING,
    REJECTED,
    APPROVED,
    OPEN,
    CLOSED,
    ABORTED,
    REOPENED,
    CREATED,
    UPDATED,
    DRAFT,
    CANCELLED,
)


class Review(BaseModel):

    STATUS_CHOICES = (
        (DRAFT, DRAFT.capitalize()),
        (OPEN, OPEN.capitalize()),
        (CLOSED, CLOSED.capitalize()),
        (ABORTED, ABORTED.capitalize()),
        (CANCELLED, CANCELLED.capitalize()),
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

    def to_json(self):
        reviewers = []
        followers = []
        for reviewer in self.reviewer_set.all():
            reviewers.append(reviewer.to_json())

        for follower in self.follower_set.all():
            followers.append(follower.to_json())

        return {
            'creator': self.creator.userprofile.name,
            'reviewers': reviewers,
            'followers': followers,
            'title': self.title,
            'description': self.description,
            'case_link': self.case_link,
            'state': self.state,
            'reviewer_state': self.reviewer_state,
            'is_public': self.is_public,
            'project': {
                'id': self.project.pk,
                'slug': self.project.slug,
                'name': self.project.name,
            },
            'reviewing_count': self.reviewing_count,
            'approved_count': self.approved_count,
            'rejected_count': self.rejected_count,
            'url': self.get_absolute_url(),
            'pk': self.pk,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

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

    # pylint: disable=too-many-arguments
    @classmethod
    def create_review(
            cls, creator, title, description,
            case_link, reviewers, project, state=OPEN,
            is_public=False, followers=None, attachments=None):
        ''' Standard review creation method '''
        obj = cls.objects.create(
            creator=creator,
            title=title,
            description=description,
            case_link=case_link,
            state=state,
            reviewer_state=REVIEWING,
            project=project,
            is_public=is_public,
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
                sort_order=attachment['sort_order'],
            )

        # Events
        if state != DRAFT:
            Event.create_event(
                project,
                EventType.DEMO_CREATED,
                obj,
                creator
            )

        for reviewer in reviewers:
            Reviewer.create_reviewer(
                obj, reviewer, creator, True, draft=state == DRAFT
            )
            UserReviewStatus.create_user_review_status(
                obj, reviewer,
            )

        for follower in followers:
            Follower.create_follower(
                obj, follower, creator, True, draft=state == DRAFT
            )
            UserReviewStatus.create_user_review_status(
                obj, follower,
            )

        # Creator UserReviewStatus, set read to True, cuz they just created it
        # so I'm assuming they read it
        UserReviewStatus.create_user_review_status(
            obj, obj.creator, True
        )

        if state == OPEN:
            obj._send_revision_messages()  # pylint: disable=protected-access
            Reminder.create_reminders_for_review(obj)
            obj.trigger_webhooks(CREATED)

        return obj

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    @classmethod
    def update_review(
            cls, review, creator, title, description,
            case_link, reviewers, project, state=OPEN,
            is_public=False, followers=None, attachments=None
        ):
        ''' Standard update review method '''
        # Figure out if we have a state transition
        obj = cls.objects.get(pk=review)
        current_state = obj.state
        obj.title = title
        obj.case_link = case_link
        obj.project = project
        obj.is_public = is_public
        obj.save()

        state_change = False
        is_update = False
        if current_state == DRAFT and state == OPEN:
            state_change = True

        if state == DRAFT or state_change:
            obj.description = description
            obj.save()
            rev = obj.revision
            rev.description = description
            rev.save()
            prev_revision = None

        if state != DRAFT and not state_change:
            is_update = True
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
                sort_order=attachment['sort_order'],
            )

        # No attachments, we'll copy them over
        if prev_revision and not attachments:
            for attachment in prev_revision.attachments.all():
                attachment.content_object = rev
                attachment.pk = None
                attachment.save()

        # Events
        if state == OPEN and not state_change:
            Event.create_event(
                project,
                EventType.DEMO_UPDATED,
                obj,
                creator
            )

        for reviewer in reviewers:
            try:
                reviewer = Reviewer.objects.get(review=obj, reviewer=reviewer)
            except Reviewer.DoesNotExist:
                reviewer = Reviewer.create_reviewer(
                    obj, reviewer, creator, True, draft=state == DRAFT
                )
            else:
                reviewer.status = REVIEWING
                reviewer.save()
                if state_change:
                    reviewer.create_reviewer_event(creator)

        for follower in followers:
            try:
                follower = Follower.objects.get(review=obj, user=follower)
            except Follower.DoesNotExist:
                Follower.create_follower(
                    review=obj, user=follower,
                    creator=creator, skip_notifications=True,
                    draft=state == DRAFT
                )
            else:
                if state_change:
                    follower.create_follower_event(creator)

        # Update UserReviewStatuses
        UserReviewStatus.objects.filter(review=obj).exclude(
            user=creator
        ).update(read=False)

        # Drop Reviewers no longer assigned
        reviewers = obj.reviewer_set.exclude(review=obj, reviewer__in=reviewers)
        skip_drop_events = state == DRAFT or state_change
        for reviewer in reviewers:
            reviewer.drop_reviewer(obj.creator, draft=skip_drop_events)
        followers = obj.follower_set.exclude(review=obj, user__in=followers)
        for follower in followers:
            follower.drop_follower(obj.creator, draft=skip_drop_events)

        if is_update:
            # pylint: disable=protected-access
            obj._send_revision_messages(update=True)
            obj.trigger_webhooks(UPDATED)
            Reminder.update_reminders_for_review(obj)

        if state_change:
            obj.update_state(state)
            obj._send_revision_messages() # pylint: disable=protected-access

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
            Event.create_event(
                self.project,
                EventType.DEMO_APPROVED,
                self,
                self.creator
            )
        elif state == REJECTED:
            Message.send_system_message(
                '"{}" has been Rejected'.format(self.title),
                'demotime/messages/rejected.html',
                {'review': self},
                self.creator,
                revision=self.revision,
            )
            Event.create_event(
                self.project,
                EventType.DEMO_REJECTED,
                self,
                self.creator
            )
        elif state == REVIEWING:
            Message.send_system_message(
                '"{}" is back Under Review'.format(self.title),
                'demotime/messages/reviewing.html',
                {'review': self, 'previous_state': previous_state},
                self.creator,
                revision=self.revision,
            )
            Event.create_event(
                self.project,
                EventType.DEMO_REVIEWING,
                self,
                self.creator
            )
        else:
            raise RuntimeError('Invalid Demo State')

    def update_reviewer_state(self):
        statuses = self.reviewer_set.values_list('status', flat=True)
        approved = all(status == APPROVED for status in statuses)
        rejected = all(status == REJECTED for status in statuses)
        reviewing = not approved and not rejected
        if approved and self.reviewer_state != APPROVED:
            self._change_reviewer_state(APPROVED)
            self.trigger_webhooks(APPROVED)
            return True, APPROVED
        elif rejected and self.reviewer_state != REJECTED:
            self._change_reviewer_state(REJECTED)
            self.trigger_webhooks(REJECTED)
            return True, REJECTED
        elif reviewing and self.reviewer_state != REVIEWING:
            self._change_reviewer_state(REVIEWING)
            return True, REVIEWING

        return False, ''

    def _open_review(self, state):
        self.state = state
        self.save(update_fields=['state', 'modified'])
        Event.create_event(
            self.project,
            EventType.DEMO_CREATED,
            self,
            self.creator
        )
        Reminder.create_reminders_for_review(self)
        return True

    def _reopen_review(self, state):
        # We take a state because this can be closed or aborted, it's okay
        # we don't judge
        prev_state = self.get_state_display()
        self.state = state
        self.save(update_fields=['state', 'modified'])
        Event.create_event(
            self.project,
            EventType.DEMO_OPENED,
            self,
            self.creator
        )
        users = User.objects.filter(
            models.Q(reviewer__review=self) | models.Q(follower__review=self),
        ).distinct()
        reviewers = self.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            Message.send_system_message(
                '"{}" has been Reopened'.format(self.title),
                'demotime/messages/reopened.html',
                {
                    'is_reviewer': is_reviewer,
                    'review': self,
                    'previous_state': prev_state,
                    'user': user
                },
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
        self.save(update_fields=['state', 'modified'])
        if state == ABORTED:
            event_type = EventType.DEMO_ABORTED
        else:
            event_type = EventType.DEMO_CLOSED
        Event.create_event(
            self.project,
            event_type,
            self,
            self.creator
        )
        users = User.objects.filter(
            models.Q(reviewer__review=self) | models.Q(follower__review=self),
        ).distinct()
        reviewers = self.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            Message.send_system_message(
                '"{}" has been {}'.format(self.title, state.capitalize()),
                'demotime/messages/closed.html',
                {
                    'is_reviewer': is_reviewer,
                    'review': self,
                    'previous_state': prev_state,
                    'user': user,
                },
                user,
                revision=self.revision,
            )

        Reminder.update_reminder_activity_for_review(self)

        return True

    def _common_state_change(self):
        ''' General purpose state change things '''
        UserReviewStatus.objects.filter(
            review=self
        ).exclude(user=self.creator).update(
            read=False
        )

    def update_state(self, new_state):
        state_changed = False
        if self.state == DRAFT and new_state == OPEN:
            state_changed = self._open_review(new_state)
            self.trigger_webhooks(CREATED)
        elif self.state == OPEN and new_state == CLOSED:
            state_changed = self._close_review(new_state)
            self.trigger_webhooks(CLOSED)
        elif self.state == OPEN and new_state == ABORTED:
            state_changed = self._close_review(new_state)
            self.trigger_webhooks(ABORTED)
        elif self.state == CLOSED and new_state == OPEN:
            state_changed = self._reopen_review(new_state)
            self.trigger_webhooks(REOPENED)
        elif self.state == ABORTED and new_state == OPEN:
            state_changed = self._reopen_review(new_state)
            self.trigger_webhooks(REOPENED)
        elif self.state == DRAFT and new_state == CLOSED:
            self.state = CANCELLED
            self.save()

        if state_changed:
            self._common_state_change()

        return state_changed

    def trigger_webhooks(self, trigger_event, additional_json=None):
        hooks = self.project.webhook_set.filter(trigger_event=trigger_event)
        for hook in hooks:
            tasks.fire_webhook.delay(self.pk, hook.pk, additional_json)

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
