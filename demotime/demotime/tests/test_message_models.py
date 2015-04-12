from demotime import models
from demotime.tests import BaseTestCase


class TestMessageModels(BaseTestCase):

    def test_create_message(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.create_message(
            receipient=self.user,
            sender=self.system_user,
            title='Test Title',
            review_revision=review.revision,
            thread=None,
            message='Test Message'
        )
        self.assertEqual(msg.receipient, self.user)
        self.assertEqual(msg.sender, self.system_user)
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.title, 'Test Title')
        self.assertEqual(msg.message, 'Test Message')

    def test_create_system_message(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.send_system_message(
            'Test Message',
            'demotime/messages/new_comment.html',
            {'receipient': self.user, 'title': 'Test Title', 'url': 'http://example.org'},
            self.user,
            revision=review.revision,
        )
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.sender.username, 'demotime_sys')
        self.assertIn('http://example.org', msg.message)
        self.assertEqual(msg.title, 'Test Message')
