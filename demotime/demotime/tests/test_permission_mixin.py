from mock import Mock

from django.contrib.auth.models import AnonymousUser

from demotime.views import CanViewMixin
from demotime import models
from demotime.tests import BaseTestCase


class TestPermissionMixin(BaseTestCase):

    def setUp(self):
        super(TestPermissionMixin, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.mixin = CanViewMixin()
        self.request = Mock()

    def test_public_project_allows_unauthed(self):
        self.project.is_public = True
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.request = self.request
        self.assertTrue(self.mixin.test_func())

    def test_non_public_project_requires_auth(self):
        self.project.is_public = False
        self.request.user = self.user
        self.user = AnonymousUser()
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        self.assertFalse(self.mixin.test_func())

    def test_user_directly_in_project(self):
        self.project.is_public = False
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()

        models.ProjectMember.objects.get_or_create(
            project=self.project, user=self.user
        )
        self.assertTrue(self.mixin.test_func())

    def test_user_in_group_in_project(self):
        self.project.is_public = False
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()

        models.ProjectGroup.objects.get_or_create(
            project=self.project, group=self.group
        )
        self.assertTrue(self.mixin.test_func())

    def test_user_not_in_group_or_project(self):
        self.project.is_public = False
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        self.assertFalse(self.mixin.test_func())

    def test_require_admin_privileges(self):
        self.project.is_public = False
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        self.mixin.require_admin_privileges = True
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()

        pm, _ = models.ProjectMember.objects.get_or_create(
            project=self.project, user=self.user
        )
        self.assertFalse(self.mixin.test_func())

        pm.is_admin = True
        pm.save()
        self.assertTrue(self.mixin.test_func())

    def test_require_admin_privileges_overrides_is_public(self):
        self.project.is_public = True
        self.request.user = self.user
        self.mixin.project = self.project
        self.mixin.review = self.review
        self.mixin.request = self.request
        self.mixin.require_admin_privileges = True
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()

        pm, _ = models.ProjectMember.objects.get_or_create(
            project=self.project, user=self.user
        )
        self.assertFalse(self.mixin.test_func())

        pm.is_admin = True
        pm.save()
        self.assertTrue(self.mixin.test_func())

    def test_require_superuser_privileges(self):
        self.user.is_superuser = True
        self.request.user = self.user
        self.mixin.project = None
        self.mixin.review = None
        self.mixin.request = self.request
        self.mixin.require_superuser_privileges = True
        self.assertTrue(self.mixin.test_func())

    def test_require_superuser_privileges_without_superuser(self):
        self.user.is_superuser = False
        self.request.user = self.user
        self.mixin.project = None
        self.mixin.review = None
        self.mixin.request = self.request
        self.mixin.require_superuser_privileges = True
        self.assertFalse(self.mixin.test_func())

    def test_require_superuser_privileges_unauthed(self):
        self.user.is_superuser = True
        self.request.user = self.user
        self.user = AnonymousUser()
        self.mixin.project = None
        self.mixin.review = None
        self.mixin.request = self.request
        self.mixin.require_superuser_privileges = True
        self.assertFalse(self.mixin.test_func())
