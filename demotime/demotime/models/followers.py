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
    def create_follower(cls, review, user, non_revision=False):
        existing_reviewer = review.reviewer_set.filter(reviewer=user)
        if existing_reviewer.exists():
            return existing_reviewer.get()

        obj, _ = cls.objects.get_or_create(
            review=review,
            user=user
        )
        if non_revision:
            obj._send_follower_message()
        return obj

    def _send_follower_message(self):
        title = '{} is now following {}'.format(
            self.display_name,
            self.review.title
        )

        context = {
            'receipient': self.review.creator,
            'url': self.review.get_absolute_url(),
            'title': self.review.title,
            'follower': self,
        }
        Message.send_system_message(
            title,
            'demotime/messages/follower.html',
            context,
            self.review.creator,
            revision=self.review.revision,
        )

    class Meta:
        unique_together = (
            ('review', 'user')
        )
