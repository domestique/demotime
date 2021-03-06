import json

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime import constants, models
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
                'name': self.test_user_2.userprofile.name,
                'username': self.test_user_2.username,
                'url': self.test_user_2.userprofile.get_absolute_url(),
            }],
            'errors': {},
            'success': True,
        })

    def test_find_reviewer_excludes_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_reviewer',
            'name': self.review.creator_set.active().get().user,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [{
                'pk': self.test_user_2.pk,
                'name': self.test_user_2.userprofile.name,
                'username': self.test_user_2.username,
                'url': self.test_user_2.userprofile.get_absolute_url(),
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
            pk=self.review.creator_set.active().get().user.pk
        )
        user_list = []
        for user in users:
            user_list.append({
                'pk': user.pk,
                'name': user.userprofile.name,
                'username': user.username,
                'url': user.userprofile.get_absolute_url(),
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
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, reviewer)

    def test_add_reviewer_to_draft(self):
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['reviewers'] = User.objects.filter(
            username__startswith='test_user_'
        )[:2]
        review_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**review_kwargs)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(draft_review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': draft_review.pk,
            'user_pk': self.test_user_2.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 0)
        reviewer = models.Reviewer.objects.get(
            review=draft_review, reviewer=self.test_user_2
        )
        self.assertEqual(reviewer.status, constants.REVIEWING)
        self.assertEqual(draft_review.reviewers.count(), 3)
        self.assertEqual(data, {
            'reviewer_name': self.test_user_2.userprofile.__str__(),
            'reviewer_user_pk': self.test_user_2.pk,
            'reviewer_status': constants.REVIEWING,
            'removed_follower': False,
            'success': True,
            'errors': {},
        })
        events = reviewer.events.filter(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertFalse(events.exists())

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
        self.assertEqual(self.review.reviewer_set.active().count(), 3)
        self.assertEqual(self.review.follower_set.active().count(), 1)
        self.assertEqual(data, {
            'reviewer_name': follower.userprofile.__str__(),
            'reviewer_user_pk': follower.pk,
            'reviewer_status': models.reviews.REVIEWING,
            'removed_follower': True,
            'success': True,
            'errors': {},
        })
        follower_obj = models.Follower.objects.get(
            user=follower, review=self.review
        )
        self.assertFalse(follower_obj.is_active)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, reviewer)

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
        })

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
        })

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
        })

    def test_add_creator_as_reviewer(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator_set.active().get().user.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'reviewer_name': '',
            'reviewer_user_pk': '',
            'reviewer_status': '',
            'success': False,
            'errors': {'user_pk': 'User already on review'}
        })

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
        self.assertEqual(
            self.review.reviewer_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.reviewer_set.get(is_active=False)
        )

    def test_delete_readd_reviewer(self):
        test_user_1 = User.objects.get(username='test_user_1')
        reviewer = models.Reviewer.objects.get(
            reviewer=test_user_1,
            review=self.review,
        )
        self.assertTrue(reviewer.is_active)
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'user_pk': test_user_1.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        reviewer.refresh_from_db()
        self.assertFalse(reviewer.is_active)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.reviewer_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.reviewer_set.get(is_active=False)
        )
        response = self.client.post(reverse('user-api'), {
            'action': 'add_reviewer',
            'review_pk': self.review.pk,
            'user_pk': test_user_1.pk
        })
        self.assertStatusCode(response, 200)
        reviewer.refresh_from_db()
        self.assertTrue(reviewer.is_active)
        self.assertEqual(
            self.review.reviewer_set.active().count(), 2
        )
        events = self.review.event_set.filter(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(events.count(), 3)
        event = events.order_by('pk').last()
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.related_object.reviewer, test_user_1)

    def test_delete_reviewer_updates_review_state(self):
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewers.count(), 2)
        models.Reviewer.objects.exclude(reviewer=test_user_1).update(
            status=constants.APPROVED
        )
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'user_pk': test_user_1.pk,
            'review_pk': self.review.pk,
        })
        self.review.refresh_from_db()
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.reviewer_set.active().count(), 1
        )
        self.assertEqual(self.review.reviewer_state, constants.APPROVED)
        event = self.review.event_set.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.reviewer_set.get(is_active=False)
        )

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
            'user_pk': self.review.creator_set.active().get().user.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
        })

    def test_delete_reviewer_not_owner_not_reviewer(self):
        ''' Test deleting a reviewer from a review you do not own nor are a
        reviewer on
        '''
        self.client.logout()
        assert self.client.login(
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

    def test_delete_self_as_reviewer(self):
        ''' Test that asserts that you can remove yourself as a reviewer '''
        self.client.logout()
        assert self.client.login(
            username='test_user_1',
            password='testing',
        )
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewers.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_reviewer',
            'review_pk': self.review.pk,
            'user_pk': test_user_1.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.reviewer_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, test_user_1)
        self.assertEqual(
            event.related_object,
            self.review.reviewer_set.get(is_active=False),
        )


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
            'name': self.review.creator_set.get().user.userprofile.name,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [
                {
                    'pk': self.test_user_2.pk,
                    'name': self.test_user_2.userprofile.name,
                    'username': self.test_user_2.username,
                    'url': self.test_user_2.userprofile.get_absolute_url(),
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
            pk=self.review.creator_set.active().get().user.pk
        )
        user_list = []
        for user in users:
            user_json = {
                'pk': user.pk,
                'name': user.userprofile.name,
                'username': user.username,
                'url': user.userprofile.get_absolute_url(),
            }
            user_list.append(user_json)
            self.assertIn(user_json, data['users'])

        self.assertEqual(len(user_list), 2)
        self.assertEqual(len(data['users']), 2)
        self.assertEqual(data['errors'], {})
        self.assertTrue(data['success'])

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
        event = follower.events.get(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, follower)

    def test_add_follower_to_draft(self):
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['reviewers'] = User.objects.filter(
            username__startswith='test_user_'
        )[:2]
        review_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**review_kwargs)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(draft_review.follower_set.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': draft_review.pk,
            'user_pk': self.test_user_2.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 0)
        follower = models.Follower.objects.get(
            review=draft_review, user=self.test_user_2
        )
        self.assertEqual(draft_review.follower_set.count(), 3)
        self.assertEqual(data, {
            'follower_name': self.test_user_2.userprofile.name,
            'follower_user_pk': self.test_user_2.pk,
            'success': True,
            'errors': {},
        })
        events = follower.events.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertFalse(events.exists())

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
        event = follower.events.get(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, extra_follower)
        self.assertEqual(event.related_object, follower)

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
        })

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
        })

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
        })

    def test_add_creator_as_follower(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'review_pk': self.review.pk,
            'user_pk': self.review.creator_set.active().get().user.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'follower_name': '',
            'follower_user_pk': '',
            'success': False,
            'errors': {'user_pk': 'User already on review'}
        })

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
        self.assertEqual(
            self.review.follower_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.FOLLOWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            models.Follower.objects.get(user=follower_0, review=self.review),
        )

    def test_delete_readd_follower(self):
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
        self.assertEqual(
            self.review.follower_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.FOLLOWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            models.Follower.objects.get(user=follower_0, review=self.review),
        )

        response = self.client.post(reverse('user-api'), {
            'action': 'add_follower',
            'user_pk': follower_0.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(
            self.review.follower_set.active().count(), 2
        )
        event = self.review.event_set.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        ).first()
        self.assertEqual(
            event.event_type.code, models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            models.Follower.objects.get(user=follower_0, review=self.review),
        )

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
            'user_pk': self.review.creator_set.active().get().user.pk,
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


class TestUserApiCreators(BaseTestCase):
    ''' Tests for the Creators functionality of the User API '''

    def setUp(self):
        super(TestUserApiCreators, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Reset our mail queue
        mail.outbox = []

    def test_find_creator_for_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'name': 'co_owner',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [{
                'pk': self.co_owner.pk,
                'name': self.co_owner.userprofile.name,
                'username': self.co_owner.username,
                'url': self.co_owner.userprofile.get_absolute_url(),
            }],
            'errors': {},
            'success': True,
        })

    def test_find_creator_excludes_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'name': self.review.creator_set.active().get().user,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        users = User.objects.exclude(
            reviewer__review=self.review
        ).exclude(
            username='demotime_sys'
        ).filter(
            username__startswith='test_user',
        ).exclude(
            pk=self.review.creator_set.active().get().user.pk
        )
        user_list = []
        for user in users:
            self.assertNotEqual(self.user.username, user.username)
            user_list.append({
                'pk': user.pk,
                'name': user.userprofile.name,
                'username': user.username,
                'url': user.userprofile.get_absolute_url(),
            })
        for user in user_list:
            self.assertIn(user, data['users'])

    def test_find_creator_missing_name(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        users = User.objects.exclude(
            reviewer__review=self.review
        ).exclude(
            username='demotime_sys'
        ).exclude(
            pk=self.review.creator_set.active().get().user.pk
        )
        user_list = []
        for user in users:
            user_list.append({
                'pk': user.pk,
                'name': user.userprofile.name,
                'username': user.username,
                'url': user.userprofile.get_absolute_url(),
            })
        for user in user_list:
            self.assertIn(user, data['users'])

    def test_find_creator_review_not_specified(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'user_pk': 1
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'errors': {
                'creator': 'Can not modify creators unless you are a creator'
            },
            'success': False,
        })

    def test_find_creator_not_in_project(self):
        # Remove all of our group members, so nobody's in the project
        self.group.groupmember_set.all().delete()
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'name': 'co_owner',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'users': [],
            'errors': {},
            'success': True,
        })

    def test_add_creator(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.creator_set.active().count(), 1)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': self.review.pk,
            'user_pk': self.co_owner.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 6) # Paused Demo
        creator = models.Creator.objects.get(
            review=self.review, user=self.co_owner
        )
        self.assertTrue(creator.active)
        self.assertEqual(self.review.creator_set.active().count(), 2)
        self.assertEqual(data, {
            'creator_name': self.co_owner.userprofile.__str__(),
            'creator_user_pk': self.co_owner.pk,
            'removed_follower': False,
            'removed_reviewer': False,
            'success': True,
            'errors': {},
        })
        event = creator.events.get(
            event_type__code=models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_add_creator_to_draft(self):
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**review_kwargs)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(draft_review.creator_set.active().count(), 1)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': draft_review.pk,
            'user_pk': self.co_owner.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 1)
        creator = models.Creator.objects.get(
            review=draft_review, user=self.co_owner
        )
        self.assertEqual(draft_review.creator_set.active().count(), 2)
        self.assertEqual(data, {
            'creator_name': self.co_owner.userprofile.__str__(),
            'creator_user_pk': self.co_owner.pk,
            'removed_follower': False,
            'removed_reviewer': False,
            'success': True,
            'errors': {},
        })
        events = creator.events.filter(
            event_type__code=models.EventType.OWNER_ADDED
        )
        self.assertFalse(events.exists())

    def test_add_follower_as_creator(self):
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.creator_set.active().count(), 1)
        self.assertEqual(self.review.follower_set.active().count(), 2)
        follower = self.review.follower_set.all()[0].user
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': self.review.pk,
            'user_pk': follower.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 6)
        creator = models.Creator.objects.get(
            review=self.review, user=follower
        )
        self.assertEqual(self.review.creator_set.active().count(), 2)
        self.assertEqual(self.review.follower_set.active().count(), 1)
        self.assertEqual(data, {
            'creator_name': follower.userprofile.__str__(),
            'creator_user_pk': follower.pk,
            'removed_follower': True,
            'removed_reviewer': False,
            'success': True,
            'errors': {},
        })
        follower_obj = models.Follower.objects.get(
            user=follower, review=self.review
        )
        self.assertFalse(follower_obj.is_active)
        event = creator.events.get(
            event_type__code=models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_add_creator_missing_user_pk(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'creator_name': '',
            'creator_user_pk': '',
            'success': False,
            'errors': {'user_pk': 'User identifier missing'}
        })

    def test_add_creator_already_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'user_pk': self.user.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'creator_name': '',
            'creator_user_pk': '',
            'success': False,
            'errors': {'user_pk': 'User already on review'}
        })

    def test_add_creator_not_found(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'user_pk': 100000,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'creator_name': '',
            'creator_user_pk': '',
            'success': False,
            'errors': {'user_pk': 'User not found'}
        })

    def test_add_reviewer_as_creator(self):
        reviewer = self.test_users[0]
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': self.review.pk,
            'user_pk': reviewer.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(mail.outbox), 7)
        creator = models.Creator.objects.get(
            review=self.review, user=reviewer
        )
        self.assertEqual(self.review.creator_set.active().count(), 2)
        self.assertEqual(self.review.reviewer_set.active().count(), 2)
        self.assertEqual(data, {
            'creator_name': reviewer.userprofile.__str__(),
            'creator_user_pk': reviewer.pk,
            'removed_follower': False,
            'removed_reviewer': True,
            'success': True,
            'errors': {},
        })
        reviewer_obj = models.Reviewer.objects.get(
            reviewer=reviewer, review=self.review
        )
        self.assertFalse(reviewer_obj.is_active)
        event = creator.events.get(
            event_type__code=models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_delete_reviewer(self):
        models.Creator.objects.create(
            user=self.co_owner,
            review=self.review,
            active=True
        )
        self.assertEqual(self.review.creator_set.active().count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'user_pk': self.co_owner.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.creator_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.creator_set.get(active=False)
        )

    def test_delete_readd_creator(self):
        creator = models.Creator.objects.create(
            user=self.co_owner,
            review=self.review,
            active=True
        )
        self.assertTrue(creator.active)
        self.assertEqual(self.review.creator_set.active().count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'user_pk': self.co_owner.pk,
            'review_pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        creator.refresh_from_db()
        self.assertFalse(creator.active)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.creator_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.creator_set.get(active=False)
        )
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'review_pk': self.review.pk,
            'user_pk': self.co_owner.pk
        })
        self.assertStatusCode(response, 200)
        creator.refresh_from_db()
        self.assertTrue(creator.active)
        self.assertEqual(
            self.review.creator_set.active().count(), 2
        )
        added_event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_ADDED
        )
        removed_event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_REMOVED
        )
        self.assertEqual(
            added_event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(added_event.related_object.user, self.co_owner)
        self.assertEqual(added_event.user, self.user)
        self.assertEqual(
            removed_event.event_type.code, models.EventType.OWNER_REMOVED
        )
        self.assertEqual(removed_event.related_object.user, self.co_owner)
        self.assertEqual(removed_event.user, self.user)

    def test_convert_reviewer_updates_review_state(self):
        test_user_1 = User.objects.get(username='test_user_1')
        self.assertEqual(self.review.reviewer_set.active().count(), 3)
        models.Reviewer.objects.exclude(reviewer=test_user_1).update(
            status=constants.APPROVED
        )
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'user_pk': test_user_1.pk,
            'review_pk': self.review.pk,
        })
        self.review.refresh_from_db()
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'creator_name': test_user_1.username,
            'creator_user_pk': test_user_1.pk,
            'removed_reviewer': True,
            'removed_follower': False,
            'errors': {}
        })
        self.assertEqual(
            self.review.reviewer_set.active().count(), 2
        )
        self.assertEqual(self.review.reviewer_state, constants.APPROVED)
        event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.creator_set.get(user=test_user_1, active=True)
        )
        # Reviewer removed
        event = self.review.event_set.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(
            event.related_object,
            self.review.reviewer_set.get(is_active=False)
        )

    def test_delete_creator_missing_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'review_pk':  self.review.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User identifier missing'}
        })

    def test_delete_creator_invalid_user(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'review_pk': self.review.pk,
            'user_pk': 100000,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not found'}
        })

    def test_delete_creator_not_on_review(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'review_pk': self.review.pk,
            'user_pk': self.co_owner.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {'user_pk': 'User not currently on review'}
        })

    def test_delete_self_as_creator(self):
        ''' Test that asserts that you can remove yourself as a creator '''
        models.Creator.objects.create(
            user=self.co_owner,
            review=self.review,
            active=True
        )
        self.client.logout()
        assert self.client.login(
            username='co_owner',
            password='testing',
        )
        self.assertEqual(self.review.creator_set.count(), 2)
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'review_pk': self.review.pk,
            'user_pk': self.co_owner.pk,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': True,
            'errors': {}
        })
        self.assertEqual(
            self.review.creator_set.active().count(), 1
        )
        event = self.review.event_set.get(
            event_type__code=models.EventType.OWNER_REMOVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_REMOVED
        )
        self.assertEqual(event.user, self.co_owner)
        self.assertEqual(
            event.related_object,
            self.review.creator_set.get(active=False),
        )

    def test_delete_self_as_creator_as_only_creator(self):
        response = self.client.post(reverse('user-api'), {
            'action': 'drop_creator',
            'review_pk': self.review.pk,
            'user_pk': self.user.pk
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {
                'creator': 'Can not remove last creator'
            }
        })

    def test_find_creator_as_non_creator(self):
        self.client.logout()
        self.client.login(
            username='test_user_2',
            password='testing'
        )
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'name': 'co_owner',
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {
                'creator': 'Can not modify creators unless you are a creator'
            }
        })

    def test_add_creator_as_non_creator(self):
        self.client.logout()
        self.client.login(
            username='test_user_2',
            password='testing'
        )
        response = self.client.post(reverse('user-api'), {
            'action': 'add_creator',
            'user_pk': self.co_owner.pk,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {
                'creator': 'Can not modify creators unless you are a creator'
            }
        })

    def test_drop_creator_as_non_creator(self):
        models.Creator.objects.create(
            user=self.co_owner,
            review=self.review,
            active=True
        )
        self.client.logout()
        self.client.login(
            username='test_user_2',
            password='testing'
        )
        response = self.client.post(reverse('user-api'), {
            'action': 'find_creator',
            'user_pk': self.co_owner.pk,
            'review_pk': self.review.pk
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'success': False,
            'errors': {
                'creator': 'Can not modify creators unless you are a creator'
            }
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
                'username': self.test_user_2.username,
                'url': self.test_user_2.userprofile.get_absolute_url(),
            }],
            'errors': {},
            'success': True,
        })

    def test_invalid_action_bad_request(self):
        response = self.client.post(reverse('user-api'), {'action': 'asdf'})
        self.assertStatusCode(response, 400)
