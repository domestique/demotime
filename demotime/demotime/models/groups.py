from django.db import models

from demotime.models.base import BaseModel


class GroupType(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return u'GroupType: {}'.format(self.slug)


class Group(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    group_type = models.ForeignKey('GroupType')
    members = models.ManyToManyField('auth.User', through='GroupMember')

    def __unicode__(self):
        return u'Group: {}'.format(self.slug)


class GroupMember(BaseModel):

    user = models.ForeignKey('auth.User')
    group = models.ForeignKey('Group')
    is_admin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'GroupMember: {} - {}'.format(
            self.group.slug,
            self.user.userprofile.name
        )
