import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from demotime import forms, models
from demotime.tests import BaseTestCase


class TestMessageViews(BaseTestCase):

    def setUp(self):
        super(TestMessageViews, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.user = User.objects.get(username='test_user_0')
        self.first_message = models.Message.objects.get(receipient=self.user)
        self.system_user = User.objects.get(username='demotime_sys')
        for x in range(0, 20):
            models.Message.create_message(
                receipient=self.user,
                sender=self.system_user,
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
        for x in range(0, 20):
            models.Message.create_message(
                receipient=self.user,
                sender=self.system_user,
                title='Inbox Testing',
                message='Inbox Message',
                review_revision=None,
                thread=None,
            )
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
        models.MessageBundle.objects.filter(
            pk__in=models.MessageBundle.objects.filter(
                owner=self.user
            ).values_list('pk', flat=True)[0:5]
        ).update(deleted=True)
        models.MessageBundle.objects.filter(
            pk__in=models.MessageBundle.objects.filter(
                owner=self.user
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
        self.assertFalse(self.first_message.bundle.read)
        second_msg = models.Message.create_message(
            receipient=self.user,
            sender=self.system_user,
            title='Inbox Testing',
            message='Inbox Message',
            review_revision=None,
            thread=None,
        )
        response = self.client.get(self.first_message.bundle.get_absolute_url())
        self.assertStatusCode(response, 200)
        self.assertTrue(response.context['object'].read)
        self.assertTrue('next_msg' in response.context)
        self.assertFalse(response.context['next_msg'].read)
        self.assertEqual(response.context['next_msg'], second_msg.bundle)

    def test_message_delete(self):
        self.assertFalse(self.first_message.bundle.deleted)
        response = self.client.get(self.first_message.bundle.get_absolute_url(), {
            'action': 'delete'
        })
        self.assertRedirects(response, reverse('inbox'))
        self.first_message = models.Message.objects.get(pk=self.first_message.pk)
        self.assertTrue(self.first_message.bundle.deleted)

    def test_mark_message_unread(self):
        self.first_message.deleted = True
        self.first_message.save()
        response = self.client.get(self.first_message.bundle.get_absolute_url(), {
            'action': 'mark-unread'
        })
        self.assertRedirects(response, reverse('inbox'))
        self.first_message = models.Message.objects.get(pk=self.first_message.pk)
        self.assertFalse(self.first_message.bundle.read)

    def test_message_detail_wrong_user(self):
        """ Test asserting that you can't view another person's messages """
        msg = models.MessageBundle.objects.get(owner__username='test_user_1')
        self.assertFalse(msg.read)
        response = self.client.get(msg.get_absolute_url())
        self.assertStatusCode(response, 404)

    def test_mark_messages_read(self):
        models.MessageBundle.objects.filter(owner=self.user).update(read=False)
        response = self.client.post(reverse('inbox'), {
            'messages': models.MessageBundle.objects.filter(
                owner=self.user).values_list('pk', flat=True),
            'action': forms.BulkMessageUpdateForm.READ,
        })
        self.assertStatusCode(response, 302)
        self.assertEqual(
            models.MessageBundle.objects.filter(owner=self.user, read=True).count(),
            models.MessageBundle.objects.filter(owner=self.user).count(),
        )

    def test_mark_messages_unread(self):
        models.MessageBundle.objects.filter(owner=self.user).update(read=True)
        response = self.client.post(reverse('inbox'), {
            'messages': models.MessageBundle.objects.filter(
                owner=self.user).values_list('pk', flat=True),
            'action': forms.BulkMessageUpdateForm.UNREAD,
        })
        self.assertStatusCode(response, 302)
        self.assertEqual(
            models.MessageBundle.objects.filter(owner=self.user, read=False).count(),
            models.MessageBundle.objects.filter(owner=self.user).count(),
        )

    def test_mark_messages_deleted(self):
        models.MessageBundle.objects.filter(owner=self.user).update(deleted=False)
        response = self.client.post(reverse('inbox'), {
            'messages': models.MessageBundle.objects.filter(
                owner=self.user).values_list('pk', flat=True),
            'action': forms.BulkMessageUpdateForm.DELETED,
        })
        self.assertStatusCode(response, 302)
        self.assertEqual(
            models.MessageBundle.objects.filter(owner=self.user, deleted=True).count(),
            models.MessageBundle.objects.filter(owner=self.user).count(),
        )

    def test_mark_messages_undeleted(self):
        models.MessageBundle.objects.filter(owner=self.user).update(deleted=True)
        response = self.client.post(reverse('inbox'), {
            'messages': models.MessageBundle.objects.filter(
                owner=self.user).values_list('pk', flat=True),
            'action': forms.BulkMessageUpdateForm.UNDELETED,
        })
        self.assertStatusCode(response, 302)
        self.assertEqual(
            models.MessageBundle.objects.filter(owner=self.user, deleted=False).count(),
            models.MessageBundle.objects.filter(owner=self.user).count(),
        )


class TestMessagesAPI(BaseTestCase):

    def setUp(self):
        super(TestMessagesAPI, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.user = User.objects.get(username='test_user_0')
        self.first_message = models.Message.objects.get(receipient=self.user)
        self.system_user = User.objects.get(username='demotime_sys')
        for x in range(0, 2):
            models.Message.create_message(
                receipient=self.user,
                sender=self.system_user,
                title='Test Title {}'.format(x),
                review_revision=self.review.revision,
                thread=None,
                message='Test Message {}'.format(x)
            )
        assert self.client.login(
            username=self.user.username,
            password='testing',
        )

    def test_messages_json_with_review(self):
        models.MessageBundle.objects.update(read=True)
        last_bundle = models.MessageBundle.objects.filter(
            owner=self.user
        ).last()
        last_bundle.read = False
        last_bundle.save()
        msg = last_bundle.message_set.last()
        msg.created = datetime.now()
        msg.save()
        response = self.client.get(
            reverse('messages-json', kwargs={'review_pk': self.review.pk})
        )
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 1,
            'bundles': [{
                'bundle_pk': last_bundle.pk,
                'messages': [{
                    'review_pk': msg.review.review.pk,
                    'review_url': msg.review.review.get_absolute_url(),
                    'thread_pk': msg.thread.pk if msg.thread else '',
                    'is_comment': msg.thread != None,
                    'review_title': msg.review.review.title,
                    'message_title': msg.title,
                    'message': msg.message,
                    'message_pk': msg.pk,
                }],
            }],
        })

    def test_messages_json_without_review(self):
        models.MessageBundle.objects.filter(
            owner=self.user
        ).update(read=False, deleted=False)
        last_bundle = models.MessageBundle.objects.filter(
            owner=self.user
        ).last()
        last_bundle.read = False
        last_bundle.save()
        msg = last_bundle.message_set.last()
        msg.created = datetime.now()
        msg.save()
        response = self.client.get(reverse('messages-json'))
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 1,
            'bundles': [{
                'bundle_pk': last_bundle.pk,
                'messages': [{
                    'review_pk': msg.review.review.pk,
                    'review_url': msg.review.review.get_absolute_url(),
                    'thread_pk': msg.thread.pk if msg.thread else '',
                    'is_comment': msg.thread != None,
                    'review_title': msg.review.review.title,
                    'message_title': msg.title,
                    'message': msg.message,
                    'message_pk': msg.pk,
                }],
            }],
        })

    def test_messages_post_bulk_read(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.user
        )
        bundles.update(read=False, deleted=False)
        assert bundles.count() > 0
        response = self.client.get(reverse('messages-json'))
        self.assertEqual(
            json.loads(response.content.decode('utf-8'))['message_count'],
            bundles.count()
        )
        response = self.client.post(reverse('messages-json'), {
            'messages': list(bundles.values_list('pk', flat=True)),
            'action': 'read',
        })
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 0,
            'bundles': [],
        })

    def test_message_post_bulk_unread(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.user
        )
        bundles.update(read=True, deleted=False)
        assert bundles.count() > 0
        response = self.client.get(reverse('messages-json'))
        self.assertEqual(
            json.loads(response.content.decode('utf-8'))['message_count'],
            0,
        )
        response = self.client.post(reverse('messages-json'), {
            'messages': list(bundles.values_list('pk', flat=True)),
            'action': 'unread',
        })
        bundle = bundles.get()
        messages = []
        for msg in bundle.message_set.all():
            messages.append({
                'review_pk': msg.review.review.pk,
                'review_url': msg.review.review.get_absolute_url(),
                'thread_pk': msg.thread.pk if msg.thread else '',
                'is_comment': msg.thread != None,
                'review_title': msg.review.review.title,
                'message_title': msg.title,
                'message': msg.message,
                'message_pk': msg.pk,
            })
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 1,
            'bundles': [{
                'bundle_pk': bundle.pk,
                'messages': messages
            }],
        })

    def test_message_post_bulk_delete(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.user
        )
        bundles.update(read=False, deleted=False)
        assert bundles.count() > 0
        response = self.client.get(reverse('messages-json'))
        self.assertEqual(
            json.loads(response.content.decode('utf-8'))['message_count'],
            bundles.count()
        )
        response = self.client.post(reverse('messages-json'), {
            'messages': list(bundles.values_list('pk', flat=True)),
            'action': 'delete',
        })
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 0,
            'bundles': [],
        })

    def test_message_post_bulk_undelete(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.user
        )
        bundles.update(read=False, deleted=True)
        assert bundles.count() > 0
        response = self.client.get(reverse('messages-json'))
        self.assertEqual(
            json.loads(response.content.decode('utf-8'))['message_count'],
            0,
        )
        response = self.client.post(reverse('messages-json'), {
            'messages': list(bundles.values_list('pk', flat=True)),
            'action': 'undelete',
        })
        bundle = bundles.get()
        messages = []
        for msg in bundle.message_set.all():
            messages.append({
                'review_pk': msg.review.review.pk,
                'review_url': msg.review.review.get_absolute_url(),
                'thread_pk': msg.thread.pk if msg.thread else '',
                'is_comment': msg.thread != None,
                'review_title': msg.review.review.title,
                'message_title': msg.title,
                'message': msg.message,
                'message_pk': msg.pk,
            })
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'message_count': 1,
            'bundles': [{
                'bundle_pk': bundle.pk,
                'messages': messages
            }],
        })

    def test_message_post_bulk_all_read(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.user
        )
        bundles.update(read=False)
        assert bundles.count() > 0
        self.client.post(reverse('messages-json'), {
            'mark_all_read': True,
            'action': 'read',
        })
        for bundle in bundles:
            self.assertTrue(bundle.read)
