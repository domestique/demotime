from django.core import mail
from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestMessageModels(BaseTestCase):

    def test_create_message(self):
        self.assertEqual(len(mail.outbox), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.create_message(
            receipient=self.user,
            sender=self.system_user,
            title='Test Create Message',
            review_revision=review.revision,
            thread=None,
            message='Test Message'
        )
        self.assertEqual(msg.receipient, self.user)
        self.assertEqual(msg.receipient, msg.bundle.owner)
        self.assertFalse(msg.bundle.read)
        self.assertFalse(msg.bundle.deleted)
        self.assertEqual(msg.sender, self.system_user)
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.title, 'Test Create Message')
        self.assertEqual(msg.message, 'Test Message')
        # 6 for the reviews created, 1 for the message we sent here
        self.assertEqual(len(mail.outbox), models.Message.objects.count())
        self.assertIn('Test Create Message', [x.subject for x in mail.outbox])

    def test_create_message_without_email(self):
        self.assertEqual(len(mail.outbox), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.create_message(
            receipient=self.user,
            sender=self.system_user,
            title='Test Create Message',
            review_revision=review.revision,
            thread=None,
            message='Test Message',
            email=False,
        )
        self.assertEqual(msg.receipient, self.user)
        self.assertEqual(msg.receipient, msg.bundle.owner)
        self.assertFalse(msg.bundle.read)
        self.assertFalse(msg.bundle.deleted)
        self.assertEqual(msg.sender, self.system_user)
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.title, 'Test Create Message')
        self.assertEqual(msg.message, 'Test Message')
        # 6 for the reviews created, 1 for the message we sent here
        self.assertEqual(len(mail.outbox), models.Message.objects.count() - 1)
        self.assertNotIn('Test Create Message', [x.subject for x in mail.outbox])

    def test_create_system_message(self):
        self.assertEqual(len(mail.outbox), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.send_system_message(
            'Test System Message',
            'demotime/messages/new_comment.html',
            {'receipient': self.user, 'title': 'Test System Message', 'url': 'http://example.org'},
            self.user,
            revision=review.revision,
        )
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.receipient, msg.bundle.owner)
        self.assertFalse(msg.bundle.read)
        self.assertFalse(msg.bundle.deleted)
        self.assertEqual(msg.sender.username, 'demotime_sys')
        self.assertIn('http://example.org', msg.message)
        self.assertEqual(msg.title, 'Test System Message')
        self.assertEqual(len(mail.outbox), models.Message.objects.count())
        self.assertIn('Test System Message', [x.subject for x in mail.outbox])

    def test_create_system_message_without_email(self):
        self.assertEqual(len(mail.outbox), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.send_system_message(
            'Test System Message',
            'demotime/messages/new_comment.html',
            {'receipient': self.user, 'title': 'Test System Message', 'url': 'http://example.org'},
            self.user,
            revision=review.revision,
            email=False,
        )
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.receipient, msg.bundle.owner)
        self.assertFalse(msg.bundle.read)
        self.assertFalse(msg.bundle.deleted)
        self.assertEqual(msg.sender.username, 'demotime_sys')
        self.assertIn('http://example.org', msg.message)
        self.assertEqual(msg.title, 'Test System Message')
        self.assertEqual(len(mail.outbox), models.Message.objects.count() - 1)
        self.assertNotIn('Test System Message', [x.subject for x in mail.outbox])

    def test_create_message_bundle(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        bundle = models.MessageBundle.create_message_bundle(
            review=review,
            owner=review.creator
        )
        self.assertEqual(bundle.review, review)
        self.assertEqual(bundle.owner, review.creator)
        self.assertFalse(bundle.read)
        self.assertFalse(bundle.deleted)

    def test_create_message_bundle_without_review(self):
        user = User.objects.get(username='test_user_0')
        bundle = models.MessageBundle.create_message_bundle(
            owner=user
        )
        self.assertEqual(bundle.review, None)
        self.assertEqual(bundle.owner, user)
        self.assertFalse(bundle.read)
        self.assertFalse(bundle.deleted)

        # Make a new bundle if no review
        new_bundle = models.MessageBundle.create_message_bundle(
            owner=user
        )
        self.assertNotEqual(bundle, new_bundle)
