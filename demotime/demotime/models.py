import os

from django.db import models
from django.template import Context, loader
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


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


class Message(BaseModel):

    receipient = models.ForeignKey('auth.User', related_name='receipient')
    sender = models.ForeignKey('auth.User', related_name='sender')
    title = models.CharField(max_length=1024)
    review = models.ForeignKey('ReviewRevision', null=True)
    thread = models.ForeignKey('CommentThread', null=True)
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Message for {}, From {}'.format(
            self.receipient.username, self.sender.username
        )

    @classmethod
    def create_message(cls, receipient, sender, title, review_revision, thread, message):
        return cls.objects.create(
            receipient=receipient,
            sender=sender,
            title=title,
            review=review_revision,
            thread=thread,
            message=message,
        )

    class Meta:
        ordering = ['-created']


class CommentThread(BaseModel):

    review_revision = models.ForeignKey('ReviewRevision')

    def __unicode__(self):
        return u'Comment Thread for Review: {}'.format(self.review)

    @classmethod
    def create_comment_thread(cls, review_revision):
        return cls.objects.create(review_revision=review_revision)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']


class Comment(BaseModel):

    commenter = models.ForeignKey('auth.User')
    comment = models.TextField()
    thread = models.ForeignKey('CommentThread')
    attachments = GenericRelation(Attachment)

    def __unicode__(self):
        return u'Comment by {} on Review: {}'.format(
            self.commenter.username, self.thread.review_revision.review.title
        )

    @classmethod
    def create_comment(cls, commenter, comment, review,
                       thread=None, attachment=None, attachment_type=None):
        if not thread:
            thread = CommentThread.create_comment_thread(review)

        obj = cls.objects.create(
            commenter=commenter,
            comment=comment,
            thread=thread
        )
        if attachment or attachment_type:
            Attachment.objects.create(
                attachment=attachment,
                attachment_type=attachment_type,
                content_object=obj,
            )

        system_user = User.objects.get(username='demotime_sys')
        users = list(review.review.reviewers.all())
        users.append(review.review.creator)
        for reviewer in users:
            if reviewer == commenter:
                continue

            msg_template = loader.get_template('demotime/messages/new_comment.html')
            context = Context({
                'receipient': reviewer,
                'sender': system_user,
                'commenter': commenter,
                'url': review.get_absolute_url(),
                'title': review.review.title,
            })
            msg_text = msg_template.render(context)
            Message.create_message(
                receipient=reviewer,
                sender=system_user,
                title='New Comment on {}'.format(review.review.title),
                thread=thread,
                review_revision=review,
                message=msg_text
            )

        return obj

    class Meta:
        ordering = ['created']
