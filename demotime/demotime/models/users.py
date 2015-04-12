import os

from django.db import models
from django.core.urlresolvers import reverse

from .base import BaseModel


def avatar_field(instance, filename):
    return os.path.join('users', str(instance.user.pk), filename)


class UserProfile(BaseModel):

    user = models.OneToOneField('auth.User')
    avatar = models.ImageField(upload_to=avatar_field, null=True, blank=True)
    bio = models.TextField()
    display_name = models.CharField(max_length=2048, blank=True, null=True)

    def __unicode__(self):
        return u'{}'.format(self.display_name or self.user.username)

    def get_absolute_url(self):
        return reverse('profile', args=[self.pk])
