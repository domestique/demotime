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
    token = models.CharField(max_length=256)

    def __str__(self):
        return 'Project {}'.format(self.name)

    def to_json(self):
        groups = []
        for group in ProjectGroup.objects.filter(project=self):
            groups.append(group.to_json())

        members = []
        for member in ProjectMember.objects.filter(project=self):
            members.append(member.to_json())

        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'groups': groups,
            'members': members,
            'is_public': self.is_public,
            'url': self.get_absolute_url(),
            'pk': self.pk,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def get_absolute_url(self):
        return reverse('project-detail', args=[self.slug])

    @property
    def project_members(self):
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

    def to_json(self):
        return {
            'project_pk': self.project.pk,
            'group': self.group.to_json(),
            'is_admin': self.is_admin,
        }


class ProjectMember(BaseModel):

    project = models.ForeignKey('Project')
    user = models.ForeignKey('auth.User')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return 'ProjectMember: {} - {}'.format(
            self.project.slug,
            self.user.userprofile.name,
        )

    def to_json(self):
        return {
            'project_pk': self.project.pk,
            'user_pk': self.user.pk,
            'username': self.user.username,
            'display_name': self.user.userprofile.name,
            'is_admin': self.is_admin,
        }
