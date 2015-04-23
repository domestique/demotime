from mock import Mock

from django.contrib.auth.models import User

from demotime import context_processors, models
from demotime.tests import BaseTestCase


class TestContextProcessors(BaseTestCase):

    def setUp(self):
        super(TestContextProcessors, self).setUp()
        models.Review.create_review(**self.default_review_kwargs)
        self.request_mock = Mock()
        self.user = User.objects.get(username='test_user_0')
        self.request_mock.user = self.user
        self.request_mock.user.is_authenticated = Mock(return_value=True)

    def test_has_unread_messages(self):
        self.assertTrue(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count(self):
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            1
        )

    def test_has_unread_messages_excludes_deleted_mail(self):
        models.Message.objects.filter(receipient=self.user).update(
            read=False,
            deleted=True
        )
        self.assertFalse(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count_excludes_deleted_mail(self):
        models.Message.objects.filter(receipient=self.user).update(
            read=False,
            deleted=True
        )
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            0
        )

    def test_has_unread_messages_unauthed(self):
        self.request_mock.user.is_authenticated = Mock(return_value=False)
        self.assertFalse(
            context_processors.has_unread_messages(self.request_mock)['has_unread_messages']
        )

    def test_unread_message_count_unauthed(self):
        self.request_mock.user.is_authenticated = Mock(return_value=False)
        self.assertEqual(
            context_processors.unread_message_count(self.request_mock)['unread_message_count'],
            0
        )
