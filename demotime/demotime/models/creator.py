from django.db import models
from django.core.exceptions import ValidationError

from demotime import constants
from demotime.models.base import BaseModel
from demotime.models import Event, EventType, Message


class CreatorManager(models.Manager):

    def active(self):
        return self.get_queryset().filter(active=True)


class Creator(BaseModel):

    user = models.ForeignKey('auth.User')
    review = models.ForeignKey('Review')
    active = models.BooleanField(default=True)

    objects = CreatorManager()

    def __str__(self):
        return 'Creator: {} - {}'.format(
            self.user.userprofile.name,
            self.review.title,
        )

    def to_json(self):
        return {
            'name': self.user.userprofile.name,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'creator_pk': self.pk,
            'review_pk': self.review.pk,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def _send_creator_message(self, removed=False):
        subject = 'You have been {} as an owner of {}'.format(
            'removed' if removed else 'added',
            self.review.title
        )
        Message.send_system_message(
            subject,
            'demotime/messages/creator.html',
            {'review': self.review, 'removed': removed},
            self.user,
            revision=self.review.revision
        )

    def _create_creator_event(self, user, removed=False):
        if removed:
            event_type = EventType.OWNER_REMOVED
        else:
            event_type = EventType.OWNER_ADDED
        return Event.create_event(
            self.review.project,
            event_type,
            self,
            user
        )

    @classmethod
    def create_creator(cls, user, review, notify=False, adding_user=None):
        obj, created = cls.objects.get_or_create(
            user=user,
            review=review,
            defaults={'active': True}
        )
        if not created and obj.active:
            # Already an active creator
            return obj

        if notify:
            # pylint: disable=protected-access
            obj._send_creator_message()
            obj._create_creator_event(adding_user)
            if not obj.review.state == constants.DRAFT:
                obj.review.update_state(constants.PAUSED)

        if not obj.active:
            obj.active = True
            obj.save(update_fields=['active', 'modified'])

        return obj

    def drop_creator(self, dropping_user):
        self.active = False
        self.save(update_fields=['active', 'modified'])
        self._send_creator_message(removed=True)
        self._create_creator_event(dropping_user, removed=True)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def clean(self):
        if self.review.creator_set.active().count() >= 2:
            raise ValidationError('Demos may have a maximum of 2 Owners')
