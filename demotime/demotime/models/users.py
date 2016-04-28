import os

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .base import BaseModel


def avatar_field(instance, filename):
    return os.path.join('users', str(instance.user.pk), filename)


class UserProxy(User):

    def is_member(self, project):
        user_list = User.objects.filter(
            models.Q(projectmember__project=project) |
            models.Q(groupmember__group__project=project)
        ).distinct()
        return user_list.filter(pk=self.pk).exists()

    def is_admin(self, project):
        admin_groups = self.groupmember_set.filter(
            group__projectgroup__project=project,
            group__projectgroup__is_admin=True
        )
        admin_user = self.projectmember_set.filter(
            project=project,
            is_admin=True
        )
        return admin_groups.exists() or admin_user.exists()

    class Meta:
        proxy = True


class UserProfile(BaseModel):

    USER = 'user'
    SYSTEM = 'system'

    USER_TYPE_CHOICES = (
        (USER, USER.capitalize()),
        (SYSTEM, SYSTEM.capitalize()),
    )

    user = models.OneToOneField('auth.User')
    avatar = models.ImageField(upload_to=avatar_field, null=True, blank=True)
    bio = models.TextField()
    display_name = models.CharField(
        max_length=2048, blank=True, null=True, unique=True
    )
    user_type = models.CharField(
        max_length=1024,
        choices=USER_TYPE_CHOICES,
        default=USER,
    )

    def __unicode__(self):
        return u'{}'.format(self.display_name or self.user.username)

    @property
    def name(self):
        return self.__unicode__()

    def get_absolute_url(self):
        return reverse('profile', args=[self.pk])


class UserReviewStatus(BaseModel):

    review = models.ForeignKey('Review')
    user = models.ForeignKey('auth.User')
    read = models.BooleanField(default=False)

    def __unicode__(self):
        return u'UserReviewStatus: {} - {}'.format(
            self.user.username,
            self.review.title
        )

    @classmethod
    def create_user_review_status(cls, review, user, read=False):
        obj, _ = cls.objects.get_or_create(review=review, user=user)
        obj.read = read
        obj.save()
        return obj
