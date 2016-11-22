from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone

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
    UPDATED,
    DRAFT,
    CANCELLED,
)
from demotime.demo_machine import DemoMachine, ReviewerMachine


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
    description = models.TextField(blank=True)
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
        for reviewer in self.reviewer_set.active():
            reviewers.append(reviewer.to_json())

        for follower in self.follower_set.active():
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

    @property
    def state_machine(self):
        if getattr(self, '_state_machine', None) and self.pk:
            return self._state_machine # pylint: disable=access-member-before-definition
        else:
            self._state_machine = DemoMachine(self) # pylint: disable=attribute-defined-outside-init

        return self._state_machine

    @property
    def reviewer_state_machine(self):
        if getattr(self, '_reviewer_state_machine', None) and self.pk:
            return self._reviewer_state_machine
        else:
            self._reviewer_state_machine = ReviewerMachine(self)

        return self._reviewer_state_machine

    def send_revision_messages(self, update=False):
        title = 'New Review: {}'.format(self.title)
        if update:
            title = 'Update on Review: {}'.format(self.title)

        for reviewer in self.reviewer_set.active():
            context = {
                'receipient': reviewer.reviewer,
                'url': self.get_absolute_url(),
                'update': update,
                'title': self.title,
            }
            Message.send_system_message(
                title,
                'demotime/messages/review.html',
                context,
                reviewer.reviewer,
                revision=self.revision,
            )

        for follower in self.follower_set.active():
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
            state=DRAFT,
            reviewer_state=REVIEWING,
            project=project,
            is_public=is_public,
        )
        obj.state_machine
        rev = ReviewRevision.objects.create(
            review=obj,
            description=obj.description,
            number=1,
        )
        for attachment in attachments:
            Attachment.create_attachment(
                attachment=attachment['attachment'],
                description=attachment['description'],
                content_object=rev,
                sort_order=attachment['sort_order'],
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

        obj.update_state(state)
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
        obj.title = title
        obj.case_link = case_link
        obj.project = project
        obj.is_public = is_public
        obj.save()

        is_or_was_draft = state == DRAFT or obj.state == DRAFT
        state_change = obj.state != state
        is_update = not is_or_was_draft

        if is_or_was_draft:
            obj.description = description
            # We want the created time to represent when the user started the
            # Demo, not when they created the draft
            obj.created = timezone.now()
            obj.save()
            rev = obj.revision
            rev.description = description
            rev.save()
            prev_revision = None

        if is_update:
            prev_revision = obj.revision
            rev_count = obj.reviewrevision_set.count()
            rev = ReviewRevision.objects.create(
                review=obj,
                description=description,
                number=rev_count + 1
            )

            # No attachments, we'll copy them over
            if not attachments:
                for attachment in prev_revision.attachments.all():
                    attachment.content_object = rev
                    attachment.pk = None
                    attachment.save()

            # Events
            Event.create_event(
                project,
                EventType.DEMO_UPDATED,
                obj,
                creator
            )

        for attachment in attachments:
            Attachment.create_attachment(
                attachment=attachment['attachment'],
                description=attachment['description'],
                content_object=rev,
                sort_order=attachment['sort_order'],
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
                reviewer.is_active = True
                reviewer.save()
                if state_change and state not in (DRAFT, CANCELLED):
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
                follower.is_active = True
                follower.save()
                if state_change and state not in (DRAFT, CANCELLED):
                    follower.create_follower_event(creator)

        # Update UserReviewStatuses
        UserReviewStatus.objects.filter(review=obj).exclude(
            user=creator
        ).update(read=False)

        # Drop Reviewers no longer assigned
        reviewers = obj.reviewer_set.exclude(review=obj, reviewer__in=reviewers)
        skip_drop_events = DRAFT in (
            state, getattr(obj.state_machine.previous_state, 'name', '')
        )
        for reviewer in reviewers:
            reviewer.drop_reviewer(obj.creator, draft=skip_drop_events)
        followers = obj.follower_set.exclude(review=obj, user__in=followers)
        for follower in followers:
            follower.drop_follower(obj.creator, draft=skip_drop_events)

        obj.state_machine.change_state(state)
        # Reviewer situation may have changed, update it
        obj.update_reviewer_state()
        if is_update:
            # This is down here so that messages get sent to the right users,
            # such as if Reviewers/Followers were removed
            obj.send_revision_messages(update=True)
            obj.trigger_webhooks(UPDATED)
            Reminder.update_reminders_for_review(obj)
            if obj.state in (CLOSED, ABORTED):
                obj.update_state(OPEN)

        return obj

    def update_reviewer_state(self):
        try:
            status = self.reviewer_set.active().values_list(
                'status', flat=True).distinct().get()
        except (Reviewer.MultipleObjectsReturned, Reviewer.DoesNotExist):
            status = REVIEWING

        changed = self.reviewer_state_machine.change_state(status)
        return changed, status if changed else ''

    def update_state(self, new_state):
        return self.state_machine.change_state(new_state)

    def trigger_webhooks(self, trigger_event, additional_json=None):
        hooks = self.project.webhook_set.filter(trigger_event=trigger_event)
        for hook in hooks:
            tasks.fire_webhook.delay(self.pk, hook.pk, additional_json)

    @property
    def revision(self):
        return self.reviewrevision_set.latest()

    @property
    def reviewing_count(self):
        return self.reviewer_set.active().filter(status=REVIEWING).count()

    @property
    def approved_count(self):
        return self.reviewer_set.active().filter(status=APPROVED).count()

    @property
    def rejected_count(self):
        return self.reviewer_set.active().filter(status=REJECTED).count()


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
