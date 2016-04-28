from mock import Mock

from django.contrib.auth.models import User

from demotime import context_processors, models
from demotime.tests import BaseTestCase


class TestContextProcessors(BaseTestCase):

    def setUp(self):
        super(TestContextProcessors, self).setUp()
        models.Review.create_review(**self.default_review_kwargs)
        self.request_mock = Mock()
        self.user = User.objects.get(username='test_user_0')
        self.request_mock.user = self.user
        self.request_mock.user.is_authenticated = Mock(return_value=True)

    def test_has_unread_messages(self):
        self.assertTrue(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count(self):
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            1
        )

    def test_has_unread_messages_excludes_deleted_mail(self):
        models.MessageBundle.objects.filter(owner=self.user).update(
            read=False,
            deleted=True
        )
        self.assertFalse(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count_excludes_deleted_mail(self):
        models.MessageBundle.objects.filter(owner=self.user).update(
            read=False,
            deleted=True
        )
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            0
        )

    def test_has_unread_messages_unauthed(self):
        self.request_mock.user.is_authenticated = Mock(return_value=False)
        self.assertFalse(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count_unauthed(self):
        self.request_mock.user.is_authenticated = Mock(return_value=False)
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            0
        )

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
