import json

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime import models
from demotime.tests import BaseTestCase


class TestUserApiReviewers(BaseTestCase):
    ''' Tests for the Reviewers functionality of the User API '''

    def setUp(self):
        super(TestUserApiReviewers, self).setUp()
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

    def test_find_reviewer_for_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'name': 'test_user',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.username,
            }],
            'errors': {},
            'success': True,
        })

    def test_find_reviewer_excludes_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'name': self.review.creator,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.username,
            }],
            'errors': {},
            'success': True,
        })

    def test_find_reviewer_missing_name(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        users = User.objects.exclude(
            reviewer__review=self.review
        ).exclude(
            username='demotime_sys'
        ).exclude(
            pk=self.review.creator.pk
        )
        user_list = []
        for user in users:
            user_list.append({
                'pk': user.pk,
                'name': user.userprofile.name
            })
        for user in user_list:
            self.assertIn(user, data['users'])

    def test_find_reviewer_review_not_specified(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'user_pk': 1
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'users': [],
            'errors': {'review': 'Find reviewer requires a Review PK'},
            'success': False,
        })

    def test_find_reviewer_not_in_project(self):
        # Remove all of our group members, so nobody's in the project
        self.group.groupmember_set.all().delete()
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'name': 'test_user',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [],
            'errors': {},
            'success': True,
        })

    def test_add_reviewer(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk,
            'user_pk': self.test_user_2.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 1)
        reviewer = models.Reviewer.objects.get(
            review=self.review, reviewer=self.test_user_2
        )
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(self.review.reviewers.count(), 3)
        self.assertEqual(data, {
            'reviewer_name': self.test_user_2.userprofile.__str__(),
            'reviewer_user_pk': self.test_user_2.pk,
            'reviewer_status': models.reviews.REVIEWING,
            'removed_follower': False,
            'success': True,
            'errors': {},
        })
        self.assertTrue(
            models.Message.objects.filter(
                title='You have been added as a reviewer on: {}'.format(self.review.title),
                receipient=self.test_user_2,
                review=reviewer.review.revision,
            ).exists()
        )

    def test_add_follower_as_reviewer(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.reviewers.count(), 2)
        self.assertEqual(self.review.follower_set.count(), 2)
        follower = self.review.follower_set.all()[0].user
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk,
            'user_pk': follower.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 1)
        reviewer = models.Reviewer.objects.get(
            review=self.review, reviewer=follower
        )
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(self.review.reviewers.count(), 3)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(data, {
            'reviewer_name': follower.userprofile.__str__(),
            'reviewer_user_pk': follower.pk,
            'reviewer_status': models.reviews.REVIEWING,
            'removed_follower': True,
            'success': True,
            'errors': {},
        })
        self.assertTrue(
            models.Message.objects.filter(
                title='You have been added as a reviewer on: {}'.format(self.review.title),
                receipient=follower,
                review=reviewer.review.revision,
            ).exists()
        )
        self.assertFalse(
            models.Follower.objects.filter(
                user=follower, review=self.review
            ).exists()
        )

    def test_add_reviewer_missing_user_pk(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }
        )

    def test_add_reviewer_already_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'user_pk': User.objects.get(username='test_user_0').pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        )

    def test_add_reviewer_not_found(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'user_pk': 100000,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }
        )

    def test_add_creator_as_reviewer(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        )

    def test_delete_reviewer(self):
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'user_pk': test_user_1.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(self.review.reviewers.count(), 1)

    def test_delete_reviewer_missing_reviewer(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk':  self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User identifier missing'}
        })

    def test_delete_reviewer_invalid_user(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk': self.review.pk,
            'user_pk': 100000,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not found'}
        })

    def test_delete_reviewer_not_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk': self.review.pk,
            'user_pk': self.test_user_2.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
        })

    def test_delete_reviewer_remove_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
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
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk': self.review.pk,
            'user_pk': test_user_1.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(self.review.reviewers.count(), 2)


class TestUserApiFollowers(BaseTestCase):
    ''' Tests for the Followers functionality of the User API '''

    def setUp(self):
        super(TestUserApiFollowers, self).setUp()
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

    def test_find_follower_excludes_creator_and_reviewers(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_follower',
            'name': self.review.creator,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [
                {
                    'pk': self.test_user_2.pk,
                    'name': self.test_user_2.username,
                }
            ],
            'errors': {},
            'success': True,
        })

    def test_find_follower_missing_name(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_follower',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        users = User.objects.exclude(reviewer__review=self.review).exclude(
            username='demotime_sys'
        ).exclude(
            follower__review=self.review
        ).exclude(
            pk=self.review.creator.pk
        )
        user_list = []
        for user in users:
            user_list.append({
                'pk': user.pk,
                'name': user.userprofile.name
            })
        self.assertEqual(data, {
                'users': user_list,
                'success': True,
                'errors': {}
            }
        )

    def test_find_follower_not_in_project(self):
        # Drop all members/groups from the project
        self.group.groupmember_set.all().delete()
        response = self.client.post(reverse('user-api'), {
            'action': 'find_follower',
            'name': 'test_user',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [],
            'errors': {},
            'success': True,
        })

    def test_add_follower(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': self.review.pk,
            'user_pk': self.test_user_2.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 1)
        follower = models.Follower.objects.get(
            review=self.review, user=self.test_user_2
        )
        self.assertEqual(self.review.follower_set.count(), 3)
        self.assertEqual(data, {
            'follower_name': self.test_user_2.userprofile.name,
            'follower_user_pk': self.test_user_2.pk,
            'success': True,
            'errors': {},
        })
        self.assertTrue(
            models.Message.objects.filter(
                title='You are now following {}'.format(
                    self.review.title
                ),
                receipient=self.test_user_2,
                review=follower.review.revision,
            ).exists()
        )

    def test_add_follower_notify_follower_and_creator(self):
        extra_follower = User.objects.create(username='extra')
        extra_follower.set_password('testing')
        extra_follower.save()

        self.client.logout()
        assert self.client.login(
            username='extra',
            password='testing'
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': self.review.pk,
            'user_pk': self.test_user_2.pk
        })
        self.assertStatusCode(response, 200)
        follower = models.Follower.objects.get(
            review=self.review, user=self.test_user_2
        )
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'follower_name': self.test_user_2.userprofile.name,
            'follower_user_pk': self.test_user_2.pk,
            'success': True,
            'errors': {},
        })
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(self.review.follower_set.count(), 3)
        self.assertTrue(
            models.Message.objects.filter(
                title='You are now following {}'.format(
                    self.review.title
                ),
                receipient=self.test_user_2,
                review=follower.review.revision,
            ).exists()
        )
        self.assertTrue(
            models.Message.objects.filter(
                title='{} is now following {}'.format(
                    self.test_user_2.userprofile.name,
                    self.review.title
                ),
                receipient=self.review.creator,
                review=follower.review.revision,
            ).exists()
        )

    def test_add_follower_missing_user_pk(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }
        )

    def test_add_follower_already_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'user_pk': User.objects.get(username='test_user_0').pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        )

    def test_add_follower_not_found(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'user_pk': 100000,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }
        )

    def test_add_creator_as_follower(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        )

    def test_delete_follower(self):
        follower_0 = User.objects.get(username='follower_0')
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'user_pk': follower_0.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(self.review.follower_set.count(), 1)

    def test_delete_follower_missing_follower(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'review_pk':  self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User identifier missing'}
        })

    def test_delete_follower_invalid_user(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'review_pk': self.review.pk,
            'user_pk': 100000,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not found'}
        })

    def test_delete_follower_not_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'review_pk': self.review.pk,
            'user_pk': self.test_user_2.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
        })

    def test_delete_follower_remove_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
        })

    def test_delete_follower_not_owner(self):
        ''' Test deleting a follower from a review you do not own '''
        self.client.logout()
        self.client.login(
            username='test_user_2',
            password='testing',
        )
        follower_0 = User.objects.get(username='follower_0')
        self.assertEqual(self.review.follower_set.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_follower',
            'review_pk': self.review.pk,
            'user_pk': follower_0.pk,
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': "Not allowed to remove others from a demo you don't own"}
        })
        self.assertEqual(self.review.follower_set.count(), 2)

    def test_find_follower_review_not_specified(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_follower',
            'user_pk': 1
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'users': [],
            'errors': {'review': 'Find follower requires a Review PK'},
            'success': False,
        })


class TestUserAPI(BaseTestCase):
    ''' Test for the general purpose parts of the User API '''

    def setUp(self):
        super(TestUserAPI, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.test_user_2 = User.objects.get(username='test_user_2')

    def test_find_user(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'search_users',
            'name': 'test_user',
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(data['success'])
        self.assertEqual(data['errors'], {})
        self.assertEqual(len(data['users']), 3)
        for user in data['users']:
            assert 'test_user_' in user['name']

    def test_find_user_display_name(self):
        self.test_user_2.userprofile.display_name = 'Tinker Tom'
        self.test_user_2.userprofile.save()
        response = self.client.post(reverse('user-api',), {
            'action': 'search_users',
            'name': 'tinker'
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.userprofile.display_name,
            }],
            'errors': {},
            'success': True,
        })

    def test_invalid_action_bad_request(self):
        response = self.client.post(reverse('user-api'), {'action': 'asdf'})
        self.assertStatusCode(response, 400)
