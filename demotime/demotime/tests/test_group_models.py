from demotime import models
from demotime.tests import BaseTestCase


class TestGroupTypeModel(BaseTestCase):

    def test_create_group_type(self):
        obj = models.GroupType.create_group_type(
            name='New Group Name', slug='new-group-name'
        )
        self.assertEqual(obj.name, 'New Group Name')
        self.assertEqual(obj.slug, 'new-group-name')


class TestGroupMemberModel(BaseTestCase):

    def test_create_group_member_admin(self):
        models.GroupMember.objects.all().delete()
        gm = models.GroupMember.create_group_member(
            user=self.user,
            group=self.group,
            is_admin=True
        )
        self.assertEqual(gm.user, self.user)
        self.assertEqual(gm.group, self.group)
        self.assertTrue(gm.is_admin)

    def test_create_group_member_non_admin(self):
        models.GroupMember.objects.all().delete()
        gm = models.GroupMember.create_group_member(
            user=self.user,
            group=self.group,
            is_admin=False,
        )
        self.assertEqual(gm.user, self.user)
        self.assertEqual(gm.group, self.group)
        self.assertFalse(gm.is_admin)

    def test_create_group_will_not_dupe(self):
        models.GroupMember.objects.all().delete()
        models.GroupMember.create_group_member(
            user=self.user,
            group=self.group,
            is_admin=False,
        )
        self.assertEqual(models.GroupMember.objects.count(), 1)
        models.GroupMember.create_group_member(
            user=self.user,
            group=self.group,
            is_admin=False,
        )
        self.assertEqual(models.GroupMember.objects.count(), 1)


class TestGroupModel(BaseTestCase):

    def test_create_group_without_members(self):
        group_type = models.GroupType.objects.get()
        obj = models.Group.create_group(
            name='New Group',
            description='Description',
            slug='new-group',
            group_type=group_type,
            members=None
        )
        self.assertEqual(obj.name, 'New Group')
        self.assertEqual(obj.description, 'Description')
        self.assertEqual(obj.slug, 'new-group')
        self.assertEqual(obj.group_type, group_type)
        self.assertFalse(models.GroupMember.objects.filter(group=obj).exists())

    def test_create_group_with_members(self):
        group_type = models.GroupType.objects.get()
        members = [{
            'user': self.user,
            'is_admin': True
        }]
        obj = models.Group.create_group(
            name='New Group',
            description='Description',
            slug='new-group',
            group_type=group_type,
            members=members,
        )
        self.assertEqual(obj.name, 'New Group')
        self.assertEqual(obj.description, 'Description')
        self.assertEqual(obj.slug, 'new-group')
        self.assertEqual(obj.group_type, group_type)
        self.assertTrue(models.GroupMember.objects.filter(group=obj).exists())
        gm = models.GroupMember.objects.get(group=obj)
        self.assertEqual(gm.user, self.user)
        self.assertTrue(gm.is_admin)
