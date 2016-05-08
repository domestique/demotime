import json

from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestGroupViews(BaseTestCase):

    def setUp(self):
        super(TestGroupViews, self).setUp()
        self.user.is_superuser = True
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.group_type = models.GroupType.objects.get()

    def _create_groups(self, count=5, members=None):
        groups = []
        for x in range(0, count):
            groups.append(
                models.Group.create_group(
                    name='test_group_{}'.format(x),
                    slug='test-group-{}'.format(x),
                    description='',
                    group_type=self.group_type,
                    members=members,
                )
            )

        return groups

    def test_group_list(self):
        self._create_groups()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['object_list'].count(),
            models.Group.objects.count()
        )

    def test_group_list_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 302)

    def test_group_list_superuser_required(self):
        self.user.is_superuser = False
        self.user.save()
        response = self.client.get(reverse('group-list'))
        self.assertStatusCode(response, 403)
