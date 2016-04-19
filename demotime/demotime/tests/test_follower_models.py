from django.core import mail

from demotime import models
from demotime.tests import BaseTestCase


class TestFollowerModels(BaseTestCase):

    def setUp(self):
        super(TestFollowerModels, self).setUp()
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['followers'] = []
        self.review = models.Review.create_review(**review_kwargs)

    def test_create_follower(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(self.review, follower)

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)

    def test_create_follower_notify_follower(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(self.review, follower, True)

        # We email on non-revision
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        self.assertTrue(
            follower.messagebundle_set.filter(
                review=self.review,
                message__title='You are now following {}'.format(self.review.title),
                read=False,
            ).exists()
        )
        self.assertFalse(
            self.review.creator.messagebundle_set.filter(
                review=self.review,
                message__title='{} is now following {}'.format(
                    follower_obj.display_name,
                    self.review.title
                ),
                read=False,
            ).exists()
        )

    def test_create_follower_notify_creator(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.followers[0]
        follower_obj = models.Follower.create_follower(self.review, follower, False, True)

        # We email on non-revision
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.review.follower_set.count(), 1)
        self.assertEqual(follower_obj.review, self.review)
        self.assertEqual(follower_obj.user, follower)
        self.assertFalse(
            follower.messagebundle_set.filter(
                review=self.review,
                message__title='You are now following {}'.format(self.review.title),
                read=False,
            ).exists()
        )
        self.assertTrue(
            self.review.creator.messagebundle_set.filter(
                review=self.review,
                message__title='{} is now following {}'.format(
                    follower_obj.display_name,
                    self.review.title
                ),
                read=False,
            ).exists()
        )

    def test_create_follower_with_reviewer(self):
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertEqual(self.review.reviewer_set.count(), 3)
        mail.outbox = []
        follower = self.test_users[0]
        follower_obj = models.Follower.create_follower(self.review, follower, True)

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.review.follower_set.count(), 0)
        self.assertTrue(isinstance(follower_obj, models.Reviewer))
