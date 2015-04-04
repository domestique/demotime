import os

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created']


def attachment_filename(instance, filename):
    ''' method for determing the path of uploads '''
    if hasattr(instance.content_object, 'review'):
        folder = instance.content_object.review.pk
    else:
        folder = instance.content_object.pk
    folder = str(folder)
    return os.path.join(folder, filename)


class Attachment(BaseModel):

    PHOTO = 'photo'
    DOCUMENT = 'document'
    MOVIE = 'movie'
    AUDIO = 'audio'
    OTHER = 'other'

    ATTACHMENT_TYPE_CHOICES = (
        (PHOTO, 'Photo'),
        (DOCUMENT, 'Document'),
        (MOVIE, 'Movie/Screencast'),
        (AUDIO, 'Audio'),
        (OTHER, 'Other'),
    )

    attachment = models.FileField(upload_to=attachment_filename)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    attachment_type = models.CharField(
        max_length=128,
        choices=ATTACHMENT_TYPE_CHOICES,
        db_index=True,
    )

    @property
    def pretty_name(self):
        ''' Just cleaning up the filename display a bit '''
        return ''.join(self.attachment.name.split('/')[1:])

    class Meta:
        index_together = [
            ('content_type', 'object_id'),
        ]


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
                content_object=rev,
            )
        for reviewer in reviewers:
            Reviewer.objects.create(
                review=obj,
                reviewer=reviewer,
                status=Reviewer.REVIEWING,
            )

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
                content_object=rev,
            )
        for reviewer in reviewers:
            Reviewer.objects.get_or_create(
                review=obj,
                reviewer=reviewer,
                defaults={'status': Reviewer.REVIEWING}
            )
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

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']


class Comment(BaseModel):

    commenter = models.ForeignKey('auth.User')
    comment = models.TextField()
    review = models.ForeignKey('ReviewRevision')
    attachments = GenericRelation(Attachment)

    def __unicode__(self):
        return u'Comment by {} on Review: {}'.format(
            self.commenter.username, self.review
        )

    @classmethod
    def create_comment(cls, commenter, comment,
                       review, attachment=None, attachment_type=None):
        obj = cls.objects.create(
            commenter=commenter,
            comment=comment,
            review=review
        )
        if attachment or attachment_type:
            Attachment.objects.create(
                attachment=attachment,
                attachment_type=attachment_type,
                content_object=obj,
            )

        return obj
