from django.core.urlresolvers import reverse

from demotime import models
from demotime.tests import BaseTestCase


class TestGroupListView(BaseTestCase):

    def setUp(self):
        super(TestGroupListView, self).setUp()
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


class TestGroupManageViews(BaseTestCase):

    def setUp(self):
        super(TestGroupManageViews, self).setUp()
        self.user.is_superuser = True
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.group_type = models.GroupType.objects.get()

    def test_create_group_get(self):
        response = self.client.get(reverse('group-manage'))
        self.assertStatusCode(response, 200)
        self.assertIn('form', response.context)

    def test_create_group(self):
        response = self.client.post(reverse('group-manage'), {
            'name': 'salty dogs',
            'slug': 'salty-dogs',
            'group_type': self.group_type.pk,
            'description': 'description',
            'members': self.test_users.values_list('pk', flat=True)
        })
        self.assertStatusCode(response, 302)
        group = models.Group.objects.get(slug='salty-dogs')
        self.assertEqual(group.name, 'salty dogs')
        self.assertEqual(group.description, 'description')
        self.assertEqual(group.group_type, self.group_type)
        self.assertTrue(models.GroupMember.objects.filter(
            group=group, user__in=self.test_users
        ).exists())

    def test_edti_group_get(self):
        response = self.client.get(reverse('group-manage'), args=[self.group.slug])
        self.assertStatusCode(response, 200)
        self.assertIn('form', response.context)
        self.assertIn('group', response.context)

    def test_edit_group(self):
        self.assertEqual(self.group.groupmember_set.count(), 6)
        response = self.client.post(reverse('group-manage', args=[self.group.slug]), {
            'name': 'Swansons',
            'slug': 'swansons',
            'group_type': self.group_type.pk,
            'description': 'this will be no fun at all',
            'members': [self.user.pk]
        })
        self.assertStatusCode(response, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.groupmember_set.count(), 1)
        self.assertEqual(self.group.name, 'Swansons')
        self.assertEqual(self.group.slug, 'swansons')
        self.assertEqual(self.group.description, 'this will be no fun at all')
