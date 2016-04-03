import json

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime import models
from demotime.tests import BaseTestCase


class TestReviewerViews(BaseTestCase):

    def setUp(self):
        super(TestReviewerViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['reviewers'] = User.objects.filter(
            username__startswith='test_user_'
        )[:2]
        self.review = models.Review.create_review(**review_kwargs)
        self.test_user_2 = User.objects.get(username='test_user_2')
        # Reset out mail queue
        mail.outbox = []

    def test_reviewer_finder(self):
        response = self.client.post(
            reverse('reviewer-finder', kwargs={'pk': self.review.pk}),
            {'reviewer_name': 'test_user'}
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewers': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.username,
            }],
            'errors': {},
            'success': True,
        })

    def test_reviewer_finder_no_review(self):
        response = self.client.post(reverse('reviewer-finder'), {
            'reviewer_name': 'test_user'
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['errors'], {})
        self.assertEqual(len(data['reviewers']), 3)
        for user in data['reviewers']:
            assert 'test_user_' in user['name']

    def test_reviewer_finder_display_name(self):
        self.test_user_2.userprofile.display_name = 'Tinker Tom'
        self.test_user_2.userprofile.save()
        response = self.client.post(
            reverse('reviewer-finder', kwargs={'pk': self.review.pk}),
            {'reviewer_name': 'tinker'}
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewers': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.userprofile.display_name,
            }],
            'errors': {},
            'success': True,
        })

    def test_reviewer_finder_excludes_creator(self):
        response = self.client.post(
            reverse('reviewer-finder', kwargs={'pk': self.review.pk}),
            {'reviewer_name': self.review.creator}
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewers': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.username,
            }],
            'errors': {},
            'success': True,
        })

    def test_reviewer_finder_missing_name(self):
        response = self.client.post(
            reverse('reviewer-finder', kwargs={'pk': self.review.pk}), {}
        )
        self.assertStatusCode(response, 400)
        data = json.loads(response.content)
        self.assertEqual(data, {
                'reviewers': [],
                'success': False,
                'errors': {'reviewer_name': 'Reviewer Name missing'}
            }
        )

    def test_add_reviewer(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(
            reverse('add-reviewer', kwargs={'pk': self.review.pk}),
            {'reviewer_pk': self.test_user_2.pk}
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(len(mail.outbox), 1)
        reviewer = models.Reviewer.objects.get(
            review=self.review, reviewer=self.test_user_2
        )
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(self.review.reviewers.count(), 3)
        self.assertEqual(data, {
            'reviewer_name': self.test_user_2.userprofile.__unicode__(),
            'reviewer_status': models.reviews.REVIEWING,
            'success': True,
            'errors': {},
        })
        self.assertTrue(
            models.Message.objects.filter(
                title='Added as reviewer on: {}'.format(self.review.title),
                receipient=self.test_user_2,
                review=reviewer.review.revision,
            ).exists()
        )

    def test_add_reviewer_missing_reviewer(self):
        response = self.client.post(
            reverse('add-reviewer', kwargs={'pk': self.review.pk}), {}
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'Reviewer identifier missing'}
            }
        )

    def test_add_reviewer_already_on_review(self):
        response = self.client.post(
            reverse('add-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': User.objects.get(username='test_user_0').pk
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'User already on review'}
            }
        )

    def test_add_reviewer_not_found(self):
        response = self.client.post(
            reverse('add-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': 100000
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'User not found'}
            }
        )

    def test_add_creator_as_reviewer(self):
        response = self.client.post(
            reverse('add-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': self.review.creator.pk
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'User already on review'}
            }
        )

    def test_delete_reviewer(self):
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': test_user_1.pk
            }
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(self.review.reviewers.count(), 1)

    def test_delete_reviewer_missing_reviewer(self):
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {}
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
            'success': False,
            'errors': {'reviewer_pk': 'Reviewer identifier missing'}
        })

    def test_delete_reviewer_invalid_user(self):
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': 10000
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
            'success': False,
            'errors': {'reviewer_pk': 'User not found'}
        })

    def test_delete_reviewer_not_on_review(self):
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': self.test_user_2.pk,
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
            'success': False,
            'errors': {'reviewer_pk': 'User not currently on review'}
        })

    def test_delete_reviewer_remove_creator(self):
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': self.review.creator.pk,
            }
        )
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
            'success': False,
            'errors': {'reviewer_pk': 'User not currently on review'}
        })

    def test_delete_reviewer_not_owner(self):
        ''' Test deleting a reviewer from a review you do not own '''
        self.client.logout()
        self.client.login(
            username='test_user_2',
            password='testing',
        )
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(
            reverse('delete-reviewer', kwargs={'pk': self.review.pk}), {
                'reviewer_pk': test_user_1.pk
            }
        )
        self.assertStatusCode(response, 404)
        self.assertEqual(self.review.reviewers.count(), 2)
