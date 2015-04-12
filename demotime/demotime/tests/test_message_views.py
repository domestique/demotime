from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestMessageViews(BaseTestCase):

    def setUp(self):
        super(TestMessageViews, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.user = User.objects.get(username='test_user_0')
        self.first_message = models.Message.objects.get(receipient=self.user)
        system_user = User.objects.get(username='demotime_sys')
        for x in range(0, 20):
            models.Message.create_message(
                receipient=self.user,
                sender=system_user,
                title='Test Title {}'.format(x),
                review_revision=self.review.revision,
                thread=None,
                message='Test Message {}'.format(x)
            )
        assert self.client.login(
            username=self.user.username,
            password='testing',
        )

    def test_inbox(self):
        response = self.client.get(reverse('inbox'))
        self.assertStatusCode(response, 200)
        object_list = response.context['object_list']
        self.assertEqual(object_list.count(), 15)
        self.assertFalse(object_list[0].read)
        self.assertEqual(
            response.context['page_obj'].paginator.num_pages,
            2
        )
        self.assertEqual(
            response.context['page_obj'].number,
            1
        )
        self.assertTrue(response.context['has_unread_messages'])
        self.assertEqual(response.context['unread_message_count'], 21)

    def test_inbox_filters_and_sorting(self):
        # I'd really prefer this be a test generator, but I couldn't get that
        # to function properly. Opted to move on for now.
        testing_matrix = (
            {'filter': '', 'sort': ''},
            {'filter': '', 'sort': 'newest'},
            {'filter': '', 'sort': 'oldest'},
            {'filter': 'deleted', 'sort': ''},
            {'filter': 'deleted', 'sort': 'newest'},
            {'filter': 'deleted', 'sort': 'oldest'},
            {'filter': 'read', 'sort': ''},
            {'filter': 'read', 'sort': 'newest'},
            {'filter': 'read', 'sort': 'oldest'},
        )
        models.Message.objects.filter(
            pk__in=models.Message.objects.filter(
                receipient=self.user
            ).values_list('pk', flat=True)[0:5]
        ).update(deleted=True)
        models.Message.objects.filter(
            pk__in=models.Message.objects.filter(
                receipient=self.user
            ).values_list('pk', flat=True)[5:10]
        ).update(read=True)
        for combo in testing_matrix:
            response = self.client.get(reverse('inbox'), combo)
            self.assertStatusCode(response, 200)
            object_list = response.context['object_list']
            if combo['filter'] == 'deleted':
                self.assertTrue(all(x.deleted for x in object_list))
            elif combo['filter'] == 'read':
                self.assertTrue(all(x.read for x in object_list))
            else:
                for obj in object_list:
                    self.assertFalse(obj.read)
                    self.assertFalse(obj.deleted)

            if combo['sort'] == 'newest':
                for count, item in enumerate(object_list):
                    if (count + 1) < len(object_list):
                        assert item.created > object_list[count + 1].created
            elif combo['sort'] == 'oldest':
                for count, item in enumerate(object_list):
                    if (count + 1) < len(object_list):
                        assert item.created < object_list[count + 1].created
            else:
                # Default sort == newest, really.
                for count, item in enumerate(object_list):
                    if (count + 1) < len(object_list):
                        assert item.created > object_list[count + 1].created

    def test_message_detail(self):
        self.assertFalse(self.first_message.read)
        response = self.client.get(self.first_message.get_absolute_url())
        self.assertStatusCode(response, 200)
        self.assertTrue(response.context['object'].read)

    def test_message_delete(self):
        self.assertFalse(self.first_message.deleted)
        response = self.client.get(self.first_message.get_absolute_url(), {
            'action': 'delete'
        })
        self.assertRedirects(response, reverse('inbox'))
        self.first_message = models.Message.objects.get(pk=self.first_message.pk)
        self.assertTrue(self.first_message.deleted)

    def test_mark_message_unread(self):
        self.first_message.deleted = True
        self.first_message.save()
        response = self.client.get(self.first_message.get_absolute_url(), {
            'action': 'mark-unread'
        })
        self.assertRedirects(response, reverse('inbox'))
        self.first_message = models.Message.objects.get(pk=self.first_message.pk)
        self.assertFalse(self.first_message.read)

    def test_message_detail_wrong_user(self):
        """ Test asserting that you can't view another person's messages """
        msg = models.Message.objects.get(receipient__username='test_user_1')
        self.assertFalse(msg.read)
        response = self.client.get(msg.get_absolute_url())
        self.assertStatusCode(response, 404)
