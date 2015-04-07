from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestMessageViews(BaseTestCase):

    def setUp(self):
        super(TestMessageViews, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.user = User.objects.get(username='test_user_0')
        self.user.set_password('testing')
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing',
        )

    def test_inbox(self):
        response = self.client.get(reverse('inbox'))
        self.assertStatusCode(response, 200)
        object_list = response.context['object_list']
        self.assertEqual(object_list.count(), 1)
        self.assertFalse(object_list[0].read)
        self.assertTrue(response.context['has_unread_messages'])
        self.assertEqual(response.context['unread_message_count'], 1)

    def test_message_detail(self):
        msg = models.Message.objects.get(receipient=self.user)
        self.assertFalse(msg.read)
        response = self.client.get(msg.get_absolute_url())
        self.assertStatusCode(response, 200)
        self.assertTrue(response.context['object'].read)

    def test_message_detail_wrong_user(self):
        """ Test asserting that you can't view another person's messages """
        msg = models.Message.objects.get(receipient__username='test_user_1')
        self.assertFalse(msg.read)
        response = self.client.get(msg.get_absolute_url())
        self.assertStatusCode(response, 404)
