from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation

from .attachments import Attachment
from .base import BaseModel
from .messages import Message
from .users import UserReviewStatus

REVIEWING = 'reviewing'
REJECTED = 'rejected'
APPROVED = 'approved'
OPEN = 'open'
CLOSED = 'closed'
ABORTED = 'aborted'


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
    title = models.CharField(max_length=1024)
    description = models.TextField()
    case_link = models.CharField(max_length=2048, blank=True)
    state = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default=OPEN, db_index=True
    )
    reviewer_state = models.CharField(
        max_length=128, choices=REVIEWER_STATE_CHOICES,
        default=REVIEWING, db_index=True
    )

    def __unicode__(self):
        return u'Review: {} by {}'.format(
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

    @classmethod
    def create_review(
            cls, creator, title, description,
            case_link, reviewers, attachments=None):
        ''' Standard review creation method '''
        obj = cls.objects.create(
            creator=creator,
            title=title,
            description=description,
            case_link=case_link,
            state=OPEN,
            reviewer_state=REVIEWING,
        )
        rev = ReviewRevision.objects.create(
            review=obj,
            description=obj.description
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
            UserReviewStatus.objects.create(
                review=obj,
                user=reviewer
            )

        # Creator UserReviewStatus, set read to True, cuz they just created it
        # so I'm assuming they read it
        UserReviewStatus.create_user_review_status(
            obj, obj.creator, True
        )

        obj._send_revision_messages()
        return obj

    @classmethod
    def update_review(
            cls, review, creator, title, description,
            case_link, reviewers, attachments=None):
        ''' Standard update review method '''
        obj = cls.objects.get(pk=review)
        obj.title = title
        obj.case_link = case_link
        obj.save()
        rev = ReviewRevision.objects.create(
            review=obj,
            description=description
        )
        for attachment in attachments:
            Attachment.objects.create(
                attachment=attachment['attachment'],
                attachment_type=attachment['attachment_type'],
                description=attachment['description'],
                content_object=rev,
            )
        for reviewer in reviewers:
            try:
                Reviewer.objects.get(review=obj, reviewer=reviewer)
            except Reviewer.DoesNotExist:
                Reviewer.create_reviewer(obj, reviewer)

        # Update UserReviewStatuses
        UserReviewStatus.objects.filter(review=review).exclude(
            user=creator
        ).update(read=False)

        # Drop people that were removed
        # TODO: Send a message here?
        Reviewer.objects.exclude(reviewer__in=reviewers).delete()

        obj._send_revision_messages()
        return obj

    def _change_reviewer_state(self, state):
        previous_state = self.get_reviewer_state_display()
        self.reviewer_state = state
        self.save(update_fields=['reviewer_state'])
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
        for reviewer in self.reviewers.all():
            Message.send_system_message(
                '"{}" has been Reopened'.format(self.title),
                'demotime/messages/reopened.html',
                {'review': self, 'previous_state': prev_state, 'reviewer': reviewer},
                reviewer,
                revision=self.revision,
            )

        return True

    def _close_review(self, state):
        # We take a state because this can be closed or aborted, it's okay
        # we don't judge
        prev_state = self.get_state_display()
        self.state = state
        self.save(update_fields=['state'])
        for reviewer in self.reviewers.all():
            Message.send_system_message(
                '"{}" has been {}'.format(self.title, state.capitalize()),
                'demotime/messages/closed.html',
                {'review': self, 'previous_state': prev_state, 'reviewer': reviewer},
                reviewer,
                revision=self.revision,
            )

        return True

    def update_state(self, new_state):
        if self.state == OPEN and new_state == CLOSED:
            return self._close_review(new_state)
        elif self.state == OPEN and new_state == ABORTED:
            return self._close_review(new_state)
        elif self.state == CLOSED and new_state == OPEN:
            return self._reopen_review(new_state)
        elif self.state == ABORTED and new_state == OPEN:
            return self._reopen_review(new_state)

        return False

    @property
    def revision(self):
        return self.reviewrevision_set.latest()


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

    @classmethod
    def create_reviewer(cls, review, reviewer):
        return cls.objects.create(
            review=review,
            reviewer=reviewer,
            status=REVIEWING
        )

    def set_status(self, status):
        self.status = status
        self.save(update_fields=['status'])
        return self.review.update_reviewer_state()


class ReviewRevision(BaseModel):

    review = models.ForeignKey('Review')
    description = models.TextField()
    attachments = GenericRelation(Attachment)

    def __unicode__(self):
        return u'Review Revision: {}'.format(self.review)

    def get_absolute_url(self):
        return reverse('review-rev-detail', kwargs={
            'pk': self.review.pk,
            'rev_pk': self.pk
        })

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']
