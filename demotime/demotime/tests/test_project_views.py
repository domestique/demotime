import json

from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestProjectViews(BaseTestCase):

    def setUp(self):
        super(TestProjectViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.admin_url = reverse('project-admin', args=[self.project.slug])
        self.dash_url = reverse('project-dashboard', args=[self.project.slug])
        self.detail_url = reverse('project-detail', args=[self.project.slug])
        self.post_data = {
            'edit_group-TOTAL_FORMS': 4,
            'edit_group-INITIAL_FORMS': 0,
            'edit_group-MIN_NUM_FORMS': 0,
            'edit_group-MAX_NUM_FORMS': 5,
            'edit_member-TOTAL_FORMS': 4,
            'edit_member-INITIAL_FORMS': 0,
            'edit_member-MIN_NUM_FORMS': 0,
            'edit_member-MAX_NUM_FORMS': 5,
            'add_member-TOTAL_FORMS': 4,
            'add_member-INITIAL_FORMS': 0,
            'add_member-MIN_NUM_FORMS': 0,
            'add_member-MAX_NUM_FORMS': 5,
            'add_group-TOTAL_FORMS': 4,
            'add_group-INITIAL_FORMS': 0,
            'add_group-MIN_NUM_FORMS': 0,
            'add_group-MAX_NUM_FORMS': 5,
        }

    def test_project_index(self):
        for x in range(0, 5):
            models.Review.create_review(**self.default_review_kwargs)

        review = models.Review.objects.last()
        review.state = constants.CLOSED
        review.save()

        response = self.client.get(self.dash_url)
        self.assertStatusCode(response, 200)
        context = response.context
        self.assertEqual(context['open_demos'].count(), 4)
        self.assertEqual(context['user_updated_demos'].count(), 5)
        self.assertEqual(context['updated_demos'].count(), 5)
        self.assertEqual(context['object'], self.project)

    def test_project_detail_requires_admin(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        pm, _ = models.ProjectMember.objects.get_or_create(
            project=self.project, user=self.user
        )
        response = self.client.get(self.detail_url)
        self.assertStatusCode(response, 403)

        pm.is_admin = True
        pm.save()
        response = self.client.get(self.detail_url)
        self.assertStatusCode(response, 200)

    def test_project_edit_view(self):
        response = self.client.get(self.admin_url)
        self.assertStatusCode(response, 200)
        context = response.context
        forms = [
            'member_formset', 'edit_member_formset',
            'group_formset', 'edit_group_formset',
            'project_form'
        ]
        for form in forms:
            self.assertIn(form, context)

    def test_edit_project(self):
        is_public = not self.project.is_public
        self.post_data.update({
            'name': 'Test Project',
            'description': 'test_edit_project',
            'is_public': is_public,
            'slug': self.project.slug,
        })
        response = self.client.post(self.admin_url, self.post_data)

        self.assertStatusCode(response, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.description, 'test_edit_project')
        self.assertEqual(self.project.is_public, is_public)

    # ProjectGroup Tests

    def test_add_groups(self):
        group_type = models.GroupType.objects.get()
        group_one = models.Group.objects.create(
            name='Group One', slug='group-one',
            description='', group_type=group_type
        )
        group_two = models.Group.objects.create(
            name='Group Two', slug='group-two',
            description='', group_type=group_type
        )
        self.post_data.update({
            'name': self.project.name,
            'description': self.project.description,
            'is_public': self.project.is_public,
            'slug': self.project.slug,
            'add_group-0-group': group_one.pk,
            'add_group-0-is_admin': True,
            'add_group-1-group': group_two.pk,
            'add_group-1-is_admin': False,
        })
        response = self.client.post(self.admin_url, self.post_data)
        self.assertStatusCode(response, 302)
        self.assertTrue(
            models.ProjectGroup.objects.filter(
                project=self.project, group=self.group
            ).exists()
        )
        pg_one = models.ProjectGroup.objects.get(
            project=self.project, group=group_one
        )
        pg_two = models.ProjectGroup.objects.get(
            project=self.project, group=group_two
        )
        self.assertTrue(pg_one.is_admin)
        self.assertFalse(pg_two.is_admin)

    def test_edit_and_delete_groups(self):
        group_type = models.GroupType.objects.get()
        group_to_delete = models.Group.objects.create(
            name='Group Delete', slug='group-delete',
            description='', group_type=group_type
        )
        group_to_promote = models.Group.objects.create(
            name='Group Promote', slug='group-promote',
            description='', group_type=group_type
        )
        group_to_demote = models.Group.objects.create(
            name='Group Demote', slug='group-demote',
            description='', group_type=group_type
        )
        models.ProjectGroup.objects.create(
            project=self.project, group=group_to_delete
        )
        models.ProjectGroup.objects.create(
            project=self.project, group=group_to_promote
        )
        models.ProjectGroup.objects.create(
            project=self.project, group=group_to_demote, is_admin=True
        )
        self.post_data.update({
            'name': self.project.name,
            'description': self.project.description,
            'is_public': self.project.is_public,
            'slug': self.project.slug,
            'edit_group-0-group': group_to_delete.pk,
            'edit_group-0-is_admin': False,
            'edit_group-0-delete': True,
            'edit_group-1-group': group_to_promote.pk,
            'edit_group-1-is_admin': True,
            'edit_group-1-delete': False,
            'edit_group-2-group': group_to_demote.pk,
            'edit_group-2-is_admin': False,
            'edit_group-2-delete': False,
        })
        response = self.client.post(self.admin_url, self.post_data)
        self.assertStatusCode(response, 302)
        self.assertFalse(models.ProjectGroup.objects.filter(
            project=self.project, group=group_to_delete).exists()
        )
        pg_promoted = models.ProjectGroup.objects.get(
            project=self.project, group=group_to_promote
        )
        pg_demoted = models.ProjectGroup.objects.get(
            project=self.project, group=group_to_demote
        )
        self.assertTrue(pg_promoted.is_admin)
        self.assertFalse(pg_demoted.is_admin)

    # ProjectMember Tests

    def test_add_members(self):
        self.assertFalse(models.ProjectMember.objects.filter(
            project=self.project,
            user__pk__in=([x.pk for x in self.followers])
        ).exists())
        member_one, member_two = self.followers
        self.post_data.update({
            'name': self.project.name,
            'description': self.project.description,
            'is_public': self.project.is_public,
            'slug': self.project.slug,
            'add_member-0-user': member_one.pk,
            'add_member-0-is_admin': True,
            'add_member-1-user': member_two.pk,
            'add_member-1-is_admin': False,
        })
        response = self.client.post(self.admin_url, self.post_data)
        self.assertStatusCode(response, 302)
        pm_one = models.ProjectMember.objects.get(
            project=self.project, user=member_one
        )
        pm_two = models.ProjectMember.objects.get(
            project=self.project, user=member_two
        )
        self.assertTrue(pm_one.is_admin)
        self.assertFalse(pm_two.is_admin)

    def test_edit_and_delete_members(self):
        user_one, user_two, user_three = self.test_users
        member_to_delete = models.ProjectMember.objects.create(
            project=self.project, user=user_one
        )
        member_to_promote = models.ProjectMember.objects.create(
            project=self.project, user=user_two
        )
        member_to_demote = models.ProjectMember.objects.create(
            project=self.project, user=user_three, is_admin=True
        )
        self.assertFalse(member_to_promote.is_admin)
        self.assertTrue(member_to_demote.is_admin)
        self.post_data.update({
            'name': self.project.name,
            'description': self.project.description,
            'is_public': self.project.is_public,
            'slug': self.project.slug,
            'edit_member-0-user': member_to_delete.user.pk,
            'edit_member-0-is_admin': False,
            'edit_member-0-delete': True,
            'edit_member-1-user': member_to_promote.user.pk,
            'edit_member-1-is_admin': True,
            'edit_member-1-delete': False,
            'edit_member-2-user': member_to_demote.user.pk,
            'edit_member-2-is_admin': False,
            'edit_member-2-delete': False,
        })
        response = self.client.post(self.admin_url, self.post_data)
        self.assertStatusCode(response, 302)
        self.assertFalse(models.ProjectMember.objects.filter(
            pk=member_to_delete.pk).exists()
        )
        member_to_promote.refresh_from_db()
        member_to_demote.refresh_from_db()
        self.assertTrue(member_to_promote.is_admin)
        self.assertFalse(member_to_demote.is_admin)

    def test_project_json_view_search_by_name_post(self):
        response = self.client.post(reverse('project-json'), {
            'name': 'default',
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data, {
            'count': 1,
            'projects': [{
                'pk': self.project.pk,
                'slug': self.project.slug,
                'description': self.project.description,
                'url': self.project.get_absolute_url(),
                'is_public': self.project.is_public,
                'name': self.project.name,
            }]
        })

    def test_project_json_view_search_by_name_get(self):
        response = self.client.get(reverse('project-json'), {
            'name': 'default',
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data, {
            'count': 1,
            'projects': [{
                'pk': self.project.pk,
                'slug': self.project.slug,
                'description': self.project.description,
                'url': self.project.get_absolute_url(),
                'is_public': self.project.is_public,
                'name': self.project.name,
            }]
        })

    def test_project_json_view_search_without_name_get(self):
        response = self.client.get(reverse('project-json'))
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data, {
            'count': 1,
            'projects': [{
                'pk': self.project.pk,
                'slug': self.project.slug,
                'description': self.project.description,
                'url': self.project.get_absolute_url(),
                'is_public': self.project.is_public,
                'name': self.project.name,
            }]
        })

    def test_project_json_view_search_without_name_post(self):
        response = self.client.post(reverse('project-json'))
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data, {
            'count': 1,
            'projects': [{
                'pk': self.project.pk,
                'slug': self.project.slug,
                'description': self.project.description,
                'url': self.project.get_absolute_url(),
                'is_public': self.project.is_public,
                'name': self.project.name,
            }]
        })

    def test_project_json_view_hides_unauthed_get(self):
        models.ProjectGroup.objects.all().delete()
        models.ProjectMember.objects.all().delete()
        response = self.client.get(reverse('project-json'))
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'count': 0, 'projects': []
        })

    def test_project_json_view_hides_unauthed_post(self):
        models.ProjectGroup.objects.all().delete()
        models.ProjectMember.objects.all().delete()
        response = self.client.post(reverse('project-json'))
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'count': 0, 'projects': []
        })
