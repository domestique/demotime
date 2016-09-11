from demotime import models
from demotime.tests import BaseTestCase


class TestGroupTypeModel(BaseTestCase):

    def test_create_group_type(self):
        obj = models.GroupType.create_group_type(
            name='New Group Name', slug='new-group-name'
        )
        self.assertEqual(obj.name, 'New Group Name')
        self.assertEqual(obj.slug, 'new-group-name')
        self.assertEqual(
            obj.__str__(),
            obj.slug
        )

    def test_to_json(self):
        group_type = models.GroupType.objects.get(slug='default-group-type')
        gt_json = group_type.to_json()
        self.assertEqual(gt_json['name'], group_type.name)
        self.assertEqual(gt_json['slug'], group_type.slug)
        self.assertEqual(gt_json['pk'], group_type.pk)


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
        self.assertEqual(
            gm.__str__(),
            'GroupMember: {} - {}'.format(
                gm.group.slug,
                gm.user.userprofile.name
            )
        )

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

    def test_to_json(self):
        member = models.GroupMember.objects.all()[0]
        member_json = member.to_json()
        self.assertEqual(member_json['user_pk'], member.user.pk)
        self.assertEqual(member_json['pk'], member.pk)
        self.assertEqual(member_json['display_name'], member.user.userprofile.name)
        self.assertEqual(member_json['username'], member.user.username)
        self.assertEqual(member_json['group_pk'], member.group.pk)
        self.assertEqual(member_json['is_admin'], member.is_admin)


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

    def test_to_json(self):
        group_json = self.group.to_json()
        self.assertEqual(group_json['name'], self.group.name)
        self.assertEqual(group_json['slug'], self.group.slug)
        self.assertEqual(group_json['description'], self.group.description)
        self.assertEqual(group_json['group_type'], self.group.group_type.to_json())
        self.assertEqual(group_json['pk'], self.group.pk)

        members = []
        for member in models.GroupMember.objects.filter(group=self.group):
            members.append(member.to_json())

        self.assertEqual(group_json['members'], members)
