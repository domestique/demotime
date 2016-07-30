import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime import models
from demotime.tests import BaseTestCase


TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


class TestProfileViews(BaseTestCase):

    def setUp(self):
        super(TestProfileViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        # Sample review
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.profile_url = reverse('profile', args=[self.user.username])
        self.edit_url = reverse('edit-profile', args=[self.user.username])
        self.image_path = os.path.join(TEST_ROOT, 'test_data', 'activate_swag.gif')

    def test_get_profile_as_self(self):
        response = self.client.get(self.profile_url)
        self.assertStatusCode(response, 200)
        self.assertIn('open_demos', response.context)
        self.assertTrue(response.context['owner_viewing'])

    def test_get_profile_as_other(self):
        other_user = User.objects.get(username='test_user_2')
        response = self.client.get(reverse('profile', args=[other_user.username]))
        self.assertStatusCode(response, 200)
        self.assertIn('open_reviews', response.context)
        self.assertFalse(response.context['owner_viewing'])

    def test_get_edit_profile(self):
        response = self.client.get(self.edit_url)
        self.assertStatusCode(response, 200)
        self.assertIn('profile_form', response.context)

    def test_get_other_edit_profile(self):
        other_user = User.objects.get(username='test_user_2')
        response = self.client.get(
            reverse('edit-profile', args=[other_user.username])
        )
        self.assertStatusCode(response, 404)

    def test_update_profile_without_password(self):
        with open(self.image_path, 'rb') as img_file:
            response = self.client.post(self.edit_url, {
                'avatar': img_file,
                'bio': 'Test Bio',
                'display_name': 'Display Name',
                'email': 'new_email@example.org',
            })
        self.assertStatusCode(response, 302)
        profile = models.UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.bio, 'Test Bio')
        self.assertEqual(profile.display_name, 'Display Name')
        self.assertEqual(profile.user.email, 'new_email@example.org')

    def test_update_profile_with_password(self):
        with open(self.image_path, 'rb') as img_file:
            response = self.client.post(self.edit_url, {
                'avatar': img_file,
                'bio': 'Test Bio',
                'display_name': 'Display Name',
                'email': 'new_email@example.org',
                'password_one': 'testing2',
                'password_two': 'testing2'
            })
        self.assertStatusCode(response, 302)
        profile = models.UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.bio, 'Test Bio')
        self.assertEqual(profile.display_name, 'Display Name')
        self.assertEqual(profile.user.email, 'new_email@example.org')
        self.client.logout()
        assert self.client.login(username=self.user.username, password='testing2')

    def test_update_profile_nonmatching_password(self):
        response = self.client.post(self.edit_url, {
            'avatar': '',
            'bio': 'Test Bio',
            'display_name': 'Display Name',
            'email': 'new_email@example.org',
            'password_one': 'testing2',
            'password_two': 'testing200000'
        })
        self.assertStatusCode(response, 200)
        form = response.context['profile_form']
        self.assertEqual(
            form.non_field_errors(),
            ['Passwords do not match']
        )
