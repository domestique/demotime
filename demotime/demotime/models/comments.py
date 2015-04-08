from django.db import models
from django.template import Context, loader
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation

from .attachments import Attachment
from .base import BaseModel
from .messages import Message


class CommentThread(BaseModel):

    review_revision = models.ForeignKey('ReviewRevision')

    def __unicode__(self):
        return u'Comment Thread for Review: {}'.format(self.review_revision)

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
    attachments = GenericRelation('Attachment')

    def __unicode__(self):
        return u'Comment by {} on Review: {}'.format(
            self.commenter.username, self.thread.review_revision.review.title
        )

    @classmethod
    def create_comment(cls, commenter, comment, review,
                       thread=None, attachment=None, attachment_type=None,
                       description=None):
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
                description=description,
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
