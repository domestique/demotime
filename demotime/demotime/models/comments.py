import re

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation

from demotime.helpers import strip_tags
from .attachments import Attachment
from .base import BaseModel
from .messages import Message
from .users import UserReviewStatus


class CommentThread(BaseModel):

    review_revision = models.ForeignKey('ReviewRevision')

    def __str__(self):
        return 'Comment Thread for Review: {}'.format(self.review_revision)

    @classmethod
    def create_comment_thread(cls, review_revision):
        return cls.objects.create(review_revision=review_revision)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']


class Comment(BaseModel):

    MENTION_REGEX = re.compile(r'@[\w\d_-]+')

    commenter = models.ForeignKey('auth.User')
    comment = models.TextField()
    thread = models.ForeignKey('CommentThread')
    attachments = GenericRelation('Attachment')

    def __str__(self):
        return 'Comment by {} on Review: {}'.format(
            self.commenter.username, self.thread.review_revision.review.title
        )

    @classmethod
    def create_comment(cls, commenter, comment, review,
                       thread=None, attachment=None, attachment_type=None,
                       description=None):
        if not thread:
            thread = CommentThread.create_comment_thread(review)

        # Find Mentions
        starts_with_mention = False
        comment_without_html = strip_tags(comment)
        mentioned_users = []
        mentions = cls.MENTION_REGEX.findall(comment_without_html)
        for mention in mentions:
            username = mention[1:] # Drop the @
            try:
                mentioned_user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass # Bad Mention, user was probably doing something else weird

            mentioned_users.append(mentioned_user.pk)
            if not starts_with_mention:
                starts_with_mention = comment_without_html.startswith(mention)

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
        if starts_with_mention:
            users = User.objects.filter(pk__in=mentioned_users)
        else:
            users = User.objects.filter(
                (
                    # Reviewers
                    models.Q(reviewer__review=review.review) |
                    # Followers
                    models.Q(follower__review=review.review) |
                    # Creator
                    models.Q(pk=review.review.creator.pk) |
                    # Mentions
                    models.Q(pk__in=mentioned_users)
                )
            ).distinct()

        for user in users:
            if user == commenter:
                continue

            UserReviewStatus.objects.filter(
                review=review.review,
                user=user,
            ).update(read=False)

            context = {
                'receipient': user,
                'sender': system_user,
                'comment': obj,
                'url': review.get_absolute_url(),
                'title': review.review.title,
            }
            Message.send_system_message(
                'New Comment on {}'.format(review.review.title),
                'demotime/messages/new_comment.html',
                context,
                user,
                revision=review,
                thread=thread,
            )

        return obj

    class Meta:
        ordering = ['created']
