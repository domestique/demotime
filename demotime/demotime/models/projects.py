from django.db import models

from demotime.models.base import BaseModel


class Project(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    groups = models.ManyToManyField('Group', through='ProjectGroup')
    members = models.ManyToManyField('auth.User', through='ProjectMember')
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Project {}'.format(self.name)

    def get_absolute_url(self):
        raise NotImplementedError()


class ProjectGroup(BaseModel):

    project = models.ForeignKey('Project')
    group = models.ForeignKey('Group')
    is_admin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'ProjectGroup: {} - {}'.format(
            self.project.slug,
            self.group.slug
        )


class ProjectMember(BaseModel):

    project = models.ForeignKey('Project')
    user = models.ForeignKey('auth.User')
    is_admin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'ProjectMember: {} - {}'.format(
            self.project.slug,
            self.user.userprofile.name,
        )
