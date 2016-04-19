from django.db import models

from .base import BaseModel
from .messages import Message


class Follower(BaseModel):

    review = models.ForeignKey('Review')
    user = models.ForeignKey('auth.User')

    @property
    def display_name(self):
        return u'{}'.format(self.user.userprofile.display_name or self.user.username)

    def __unicode__(self):
        return u'{} Follower on {}'.format(
            self.display_name,
            self.review.title,
        )

    @classmethod
    def create_follower(cls, review, user, notify_follower=False, notify_creator=False):
        existing_reviewer = review.reviewer_set.filter(reviewer=user)
        if existing_reviewer.exists():
            return existing_reviewer.get()

        obj, _ = cls.objects.get_or_create(
            review=review,
            user=user
        )
        if notify_follower:
            obj._send_follower_message(notify_follower=True)

        if notify_creator:
            obj._send_follower_message(notify_creator=True)

        return obj

    def _send_follower_message(self, notify_follower=False, notify_creator=False):
        if not notify_follower and not notify_creator:
            raise Exception('No receipient for message in follower message')

        title_template = '{} {} now following {}'
        title = title_template.format(
            self.display_name,
            'is',
            self.review.title
        )

        receipient = self.review.creator
        if notify_follower:
            receipient = self.user
            title = title_template.format(
                'You',
                'are',
                self.review.title
            )

        context = {
            'receipient': receipient,
            'url': self.review.get_absolute_url(),
            'title': self.review.title,
            'follower': self,
            'is_follower': notify_follower,
        }
        Message.send_system_message(
            title,
            'demotime/messages/follower.html',
            context,
            receipient,
            revision=self.review.revision,
        )

    class Meta:
        unique_together = (
            ('review', 'user')
        )