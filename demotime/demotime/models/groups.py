from django.db import models

from demotime.models.base import BaseModel


class GroupType(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return u'GroupType: {}'.format(self.slug)

    @classmethod
    def create_group_type(cls, name, slug):
        return cls.objects.create(
            name=name, slug=slug
        )


class Group(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    group_type = models.ForeignKey('GroupType')
    members = models.ManyToManyField('auth.User', through='GroupMember')

    def __unicode__(self):
        return u'Group: {}'.format(self.slug)

    @classmethod
    def create_group(cls, name, slug, description, group_type, members=None):
        members = members or []
        obj = cls.objects.create(
            name=name,
            slug=slug,
            description=description,
            group_type=group_type,
        )
        for member in members:
            GroupMember.create_group_member(
                user=member['user'],
                group=obj,
                is_admin=member['is_admin']
            )
        return obj


class GroupMember(BaseModel):

    user = models.ForeignKey('auth.User')
    group = models.ForeignKey('Group')
    is_admin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'GroupMember: {} - {}'.format(
            self.group.slug,
            self.user.userprofile.name
        )

    @classmethod
    def create_group_member(cls, user, group, is_admin=False):
        obj = cls.objects.create(
            user=user,
            group=group,
            is_admin=is_admin
        )
        return obj
