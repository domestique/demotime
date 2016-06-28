from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestProjectModels(BaseTestCase):

    def test_project_str(self):
        self.assertEqual(
            self.project.__str__(),
            'Project {}'.format(self.project.name)
        )

    def test_project_url(self):
        self.assertEqual(
            self.project.get_absolute_url(),
            '/projects/{}/admin/'.format(self.project.slug)
        )

    def test_project_members(self):
        member_pks = list(
            self.project.members.order_by('pk').values_list('pk', flat=True)
        )
        user_pks = list(
            User.objects.filter(
                userprofile__user_type=models.UserProfile.USER
            ).order_by('pk').values_list('pk', flat=True)
        )
        self.assertEqual(member_pks, user_pks)

    def test_project_to_json(self):
        proj_json = self.project._to_json()
        self.assertEqual(proj_json['name'], self.project.name)
        self.assertEqual(proj_json['slug'], self.project.slug)
        self.assertEqual(proj_json['description'], self.project.description)
        self.assertEqual(proj_json['is_public'], self.project.is_public)
        self.assertEqual(proj_json['url'], self.project.get_absolute_url())
        self.assertEqual(proj_json['pk'], self.project.pk)

        members = []
        groups = []
        for member in models.ProjectMember.objects.filter(project=self.project):
            members.append(member._to_json())

        for group in models.ProjectGroup.objects.filter(project=self.project):
            groups.append(group._to_json())

    def test_project_member_to_json(self):
        member = models.ProjectMember.objects.create(
            user=self.user,
            project=self.project
        )
        mem_json = member._to_json()
        self.assertEqual(mem_json['project_pk'], self.project.pk)
        self.assertEqual(mem_json['user_pk'], self.user.pk)
        self.assertEqual(mem_json['username'], self.user.username)
        self.assertEqual(mem_json['display_name'], self.user.userprofile.name)
        self.assertEqual(mem_json['is_admin'], member.is_admin)
