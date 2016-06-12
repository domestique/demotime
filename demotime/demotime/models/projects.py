from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime.models.base import BaseModel


class Project(BaseModel):

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    groups = models.ManyToManyField('Group', through='ProjectGroup')
    members = models.ManyToManyField('auth.User', through='ProjectMember')
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return 'Project {}'.format(self.name)

    def get_absolute_url(self):
        return reverse('project-detail', args=[self.slug])

    @property
    def members(self):
        return User.objects.filter(
            models.Q(projectmember__project=self) |
            models.Q(group__projectgroup__project=self)
        ).distinct().order_by('username')


class ProjectGroup(BaseModel):

    project = models.ForeignKey('Project')
    group = models.ForeignKey('Group')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return 'ProjectGroup: {} - {}'.format(
            self.project.slug,
            self.group.slug
        )


class ProjectMember(BaseModel):

    project = models.ForeignKey('Project')
    user = models.ForeignKey('auth.User')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return 'ProjectMember: {} - {}'.format(
            self.project.slug,
            self.user.userprofile.name,
        )
