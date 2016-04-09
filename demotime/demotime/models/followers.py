from django.db import models

from .base import BaseModel
from .messages import Message
from .reviews import Reviewer


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
    def create_follower(cls, review, user, notify_creator=False, notify_follower=False):
        existing_reviewer = Reviewer.objects.filter(review=review, reviewer=user)
        if existing_reviewer.exists():
            return existing_reviewer.get()

        obj, _ = cls.objects.get_or_create(
            review=review,
            user=user
        )
        return user
