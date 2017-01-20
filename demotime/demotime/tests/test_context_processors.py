from mock import Mock

from django.contrib.auth.models import AnonymousUser

from demotime import context_processors, models
from demotime.tests import BaseTestCase


class TestContextProcessors(BaseTestCase):

    def setUp(self):
        super(TestContextProcessors, self).setUp()
        models.Review.create_review(**self.default_review_kwargs)
        self.request_mock = Mock()
        self.user = models.UserProxy.objects.get(username='test_user_0')
        self.request_mock.user = self.user

    def test_available_projects_no_projects(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        projects = context_processors.available_projects(
            self.request_mock
        )['available_projects']
        self.assertEqual(
            list(projects),
            list(models.Project.objects.none())
        )

    def test_available_projects_in_group(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        models.ProjectGroup.objects.create(
            group=self.group,
            project=self.project
        )
        projects = context_processors.available_projects(
            self.request_mock
        )['available_projects']
        self.assertEqual(
            list(projects.values_list('pk', flat=True)),
            list(models.Project.objects.filter(pk=self.project.pk).values_list('pk', flat=True))
        )

    def test_available_projects_direct_member(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        models.ProjectMember.objects.create(
            project=self.project,
            user=self.user,
        )
        projects = context_processors.available_projects(
            self.request_mock
        )['available_projects']
        self.assertEqual(
            list(projects.values_list('pk', flat=True)),
            list(models.Project.objects.filter(pk=self.project.pk).values_list('pk', flat=True))
        )

    def test_available_projects_unauthed(self):
        self.request_mock.user = AnonymousUser()
        projects = context_processors.available_projects(
            self.request_mock
        )['available_projects']
        self.assertEqual(
            list(projects),
            list(models.Project.objects.none())
        )
