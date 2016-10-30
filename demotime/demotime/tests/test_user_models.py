from demotime import models
from demotime.tests import BaseTestCase


class TestUserModels(BaseTestCase):

    def setUp(self):
        super(TestUserModels, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)

    def test_create_user_review_status(self):
        status = models.UserReviewStatus.create_user_review_status(
            self.review,
            self.user
        )
        self.assertEqual(status.review, self.review)
        self.assertEqual(status.user, self.user)
        self.assertFalse(status.read)

    def test_create_user_review_status_read(self):
        status = models.UserReviewStatus.create_user_review_status(
            self.review,
            self.user,
            True
        )
        self.assertEqual(status.review, self.review)
        self.assertEqual(status.user, self.user)
        self.assertTrue(status.read)

    def test_absolute_url(self):
        self.assertEqual(
            self.user.userprofile.get_absolute_url(),
            '/accounts/profile/{}/'.format(self.user.username)
        )
