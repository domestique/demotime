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
        response = self.client.post(self.admin_url, {
            'name': 'Test Project',
            'description': 'test_edit_project',
            'is_public': is_public,
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
        })
        self.assertStatusCode(response, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.description, 'test_edit_project')
        self.assertEqual(self.project.is_public, is_public)
