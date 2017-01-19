from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone

from demotime.models.base import BaseModel
from demotime.models import (
    Attachment,
    Creator,
    Event,
    EventType,
    Issue,
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
    PAUSED,
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
        (PAUSED, PAUSED.capitalize()),
    )

    REVIEWER_STATE_CHOICES = (
        (REVIEWING, REVIEWING.capitalize()),
        (APPROVED, APPROVED.capitalize()),
        (REJECTED, REJECTED.capitalize()),
    )

    creators = models.ManyToManyField(
        'auth.User',
        related_name='creators',
        through='Creator',
    )
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
    title = models.CharField(max_length=1024, blank=True)
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
    last_action_by = models.ForeignKey('auth.User')

    def __str__(self):
        return 'Review: {}'.format(
            self.title
        )

    def to_json(self):
        reviewers = []
        followers = []
        creators = []
        approved_count = rejected_count = reviewing_count = 0
        for reviewer in self.reviewer_set.active().select_related(
                'reviewer', 'reviewer__userprofile'):
            reviewers.append(reviewer.to_json())
            if reviewer.status == APPROVED:
                approved_count += 1
            elif reviewer.status == REJECTED:
                rejected_count += 1
            else:
                reviewing_count += 1

        for follower in self.follower_set.active().select_related(
                'user', 'user__userprofile'):
            followers.append(follower.to_json())

        for creator in self.creator_set.active().select_related(
                'user', 'user__userprofile'):
            creators.append(creator.to_json())

        active_issues_count = Issue.objects.filter(
            review=self, resolved_by=None
        ).count()
        resolved_issues_count = Issue.objects.filter(
            review=self, resolved_by__isnull=False
        ).count()

        return {
            'creators': creators,
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
            'reviewing_count': reviewing_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'active_issues_count': active_issues_count,
            'resolved_issues_count': resolved_issues_count,
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

            for creator in self.creator_set.active().exclude(
                    user=self.last_action_by):
                context = {
                    'receipient': creator.user,
                    'url': self.get_absolute_url(),
                    'update': update,
                    'title': self.title,
                    'is_creator': True,
                }
                Message.send_system_message(
                    title,
                    'demotime/messages/review.html',
                    context,
                    creator.user,
                    revision=self.revision,
                )

        for reviewer in self.reviewer_set.active():
            context = {
                'receipient': reviewer.reviewer,
                'url': self.get_absolute_url(),
                'update': update,
                'title': self.title,
                'is_reviewer': True
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
            cls, creators, title, description,
            case_link, reviewers, project, state=OPEN,
            is_public=False, followers=None, attachments=None):
        ''' Standard review creation method '''
        owner = creators[0]
        obj = cls.objects.create(
            title=title,
            description=description,
            case_link=case_link,
            state=DRAFT,
            reviewer_state=REVIEWING,
            project=project,
            is_public=is_public,
            last_action_by=owner
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

        Creator.create_creator(
            user=owner, review=obj
        )
        if len(creators) > 1:
            co_owner = creators[1]
            Creator.create_creator(
                user=co_owner, review=obj, notify=True, adding_user=owner
            )
            UserReviewStatus.create_user_review_status(
                obj, co_owner,
            )

        for reviewer in reviewers:
            Reviewer.create_reviewer(
                obj, reviewer, owner, True, draft=True
            )
            UserReviewStatus.create_user_review_status(
                obj, reviewer,
            )

        for follower in followers:
            Follower.create_follower(
                obj, follower, owner, True, draft=True
            )
            UserReviewStatus.create_user_review_status(
                obj, follower,
            )

        # Creator UserReviewStatus, set read to True, cuz they just created it
        # so I'm assuming they read it
        UserReviewStatus.create_user_review_status(
            obj, owner, True
        )

        obj.update_state(state)
        tasks.post_process_revision.delay(rev.pk)
        tasks.post_process_review.delay(obj.pk)
        return obj

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    @classmethod
    def update_review(
            cls, review, creators, title, description,
            case_link, reviewers, project, state=OPEN,
            is_public=False, followers=None, attachments=None,
            delete_attachments=None,
        ):
        ''' Standard update review method '''
        # Figure out if we have a state transition
        owner = creators[0]
        obj = cls.objects.get(pk=review)
        obj.last_action_by = owner
        obj.title = title
        obj.case_link = case_link
        obj.project = project
        obj.is_public = is_public
        obj.save()

        is_or_was_draft = state == DRAFT or obj.state == DRAFT
        state_change = obj.state != state
        is_update = not is_or_was_draft
        attachment_offset = 0
        delete_attachments = delete_attachments if delete_attachments else []

        dropped_creators = obj.creator_set.exclude(review=obj, user__in=creators)
        for dropped_creator in dropped_creators:
            dropped_creator.drop_creator(owner)

        Creator.create_creator(
            user=owner, review=obj
        )
        if len(creators) > 1:
            co_owner = creators[1]
            _, created = Creator.create_creator(
                user=co_owner, review=obj, notify=True, adding_user=owner
            )
            # Let's flip to Paused if this demo isn't a draft and we have a
            # new creator
            if created and not is_or_was_draft:
                state = PAUSED

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
            attachment_offset = rev.attachments.aggregate(
                Max('sort_order')
            )['sort_order__max'] or 0

        if is_update:
            prev_revision = obj.revision
            rev_count = obj.reviewrevision_set.count()
            rev = ReviewRevision.objects.create(
                review=obj,
                description=description,
                number=rev_count + 1
            )

            # Copy over attachments that weren't removed
            for attachment in prev_revision.attachments.all():
                if attachment not in delete_attachments:
                    attachment.content_object = rev
                    attachment.pk = None
                    attachment.sort_order = attachment_offset
                    attachment.save()
                    attachment_offset += 1

            # Events
            Event.create_event(
                project,
                EventType.DEMO_UPDATED,
                obj,
                owner
            )

        for attachment in attachments:
            Attachment.create_attachment(
                attachment=attachment['attachment'],
                description=attachment['description'],
                content_object=rev,
                sort_order=int(attachment['sort_order']) + attachment_offset,
            )

        for reviewer in reviewers:
            try:
                reviewer = Reviewer.objects.get(review=obj, reviewer=reviewer)
            except Reviewer.DoesNotExist:
                reviewer = Reviewer.create_reviewer(
                    obj, reviewer, owner, True, draft=is_or_was_draft
                )
            else:
                reviewer.status = REVIEWING
                reviewer.is_active = True
                reviewer.save()
                if state_change and state not in (DRAFT, CANCELLED) and not is_or_was_draft:
                    reviewer.create_reviewer_event(owner)

        for follower in followers:
            try:
                follower = Follower.objects.get(review=obj, user=follower)
            except Follower.DoesNotExist:
                Follower.create_follower(
                    review=obj, user=follower,
                    creator=owner, skip_notifications=True,
                    draft=is_or_was_draft
                )
            else:
                follower.is_active = True
                follower.save()
                if state_change and state not in (DRAFT, CANCELLED) and not is_or_was_draft:
                    follower.create_follower_event(owner)

        # Update UserReviewStatuses
        UserReviewStatus.objects.filter(review=obj).exclude(
            user=owner
        ).update(read=False)

        # Drop Reviewers no longer assigned
        reviewers = obj.reviewer_set.active().exclude(review=obj, reviewer__in=reviewers)
        for reviewer in reviewers:
            reviewer.drop_reviewer(owner, draft=is_or_was_draft)
        followers = obj.follower_set.active().exclude(review=obj, user__in=followers)
        for follower in followers:
            follower.drop_follower(owner, draft=is_or_was_draft)

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

        tasks.post_process_revision.delay(rev.pk)
        tasks.post_process_review.delay(obj.pk)
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

    @property
    def open_issue_count(self):
        return self.issue_set.open().count()

    @property
    def resolved_issue_count(self):
        return self.issue_set.resolved().count()


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
