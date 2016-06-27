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
