from django.db import models
from django.template import Context, loader
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation

from .attachments import Attachment
from .base import BaseModel
from .messages import Message


class Review(BaseModel):

    OPEN = 'open'
    CLOSED = 'closed'

    STATUS_CHOICES = (
        (OPEN, 'Open'),
        (CLOSED, 'Closed')
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
    status = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default='open', db_index=True
    )

    def __unicode__(self):
        return u'Review: {} by {}'.format(
            self.title, self.creator.username
        )

    def get_absolute_url(self):
        return self.revision.get_absolute_url()

    def _send_messages(self, update=False):
        system_user = User.objects.get(username='demotime_sys')
        title = 'New Review: {}'.format(self.title)
        if update:
            title = 'Update on Review: {}'.format(self.title)

        for reviewer in self.reviewers.all():
            msg_template = loader.get_template('demotime/messages/review.html')
            context = Context({
                'receipient': reviewer,
                'sender': system_user,
                'url': self.get_absolute_url(),
                'update': update,
                'title': self.title,
            })
            msg_text = msg_template.render(context)
            Message.create_message(
                receipient=reviewer,
                sender=system_user,
                title=title,
                review_revision=self.revision,
                message=msg_text,
                thread=None,
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
            status=cls.OPEN,
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
            Reviewer.objects.create(
                review=obj,
                reviewer=reviewer,
                status=Reviewer.REVIEWING,
            )

        obj._send_messages()
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
            Reviewer.objects.get_or_create(
                review=obj,
                reviewer=reviewer,
                defaults={'status': Reviewer.REVIEWING}
            )

        obj._send_messages()
        return obj

    @property
    def revision(self):
        return self.reviewrevision_set.latest()


class Reviewer(BaseModel):

    REVIEWING = 'reviewing'
    REJECTED = 'rejected'
    ACCEPTED = 'accepted'

    STATUS_CHOICES = (
        (REVIEWING, 'Reviewing'),
        (REJECTED, 'Rejected'),
        (ACCEPTED, 'Accepted')
    )

    review = models.ForeignKey('Review')
    reviewer = models.ForeignKey('auth.User')
    status = models.CharField(
        max_length=128, choices=STATUS_CHOICES,
        default='reviewing', db_index=True
    )


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
