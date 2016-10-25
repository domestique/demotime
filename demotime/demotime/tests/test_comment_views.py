import json

from django.core import mail
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestCommentViews(BaseTestCase):

    def setUp(self):
        super(TestCommentViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        # Sample review
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachment=File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            description='Test Description',
        )
        # Reset out mail queue
        mail.outbox = []

    def test_comment_on_review(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse('review-detail', args=[self.project.slug, self.review.pk]),
            {
                'comment': "Oh nice demo!",
                'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'description': 'Test Description',
                'sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        rev = self.review.revision
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(
            rev.commentthread_set.latest().comment_set.count(),
            1
        )
        comment = rev.commentthread_set.latest().comment_set.get()
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Oh nice demo!')
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.attachment_type, constants.IMAGE)
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            10
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        self.assertEqual(len(mail.outbox), 5)
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_reply_to_comment(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse('review-detail', args=[self.project.slug, self.review.pk]),
            {'comment': "Oh nice demo!"},
        )
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(len(mail.outbox), 5)

        thread = rev.commentthread_set.latest()
        response = self.client.post(
            reverse('review-detail', args=[self.project.slug, self.review.pk]),
            {'comment': "Reply!", 'thread': thread.pk}
        )
        self.assertStatusCode(response, 302)
        # Still just 1 thread
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(thread.comment_set.count(), 2)
        self.assertTrue(thread.comment_set.filter(comment='Reply!').exists())
        self.assertEqual(len(mail.outbox), 10)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.COMMENT_ADDED
            ).count(),
            3
        )

    def test_create_second_thread(self):
        response = self.client.post(
            reverse('review-detail', args=[self.project.slug, self.review.pk]),
            {'comment': "Oh nice demo!"},
        )
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 2)

        thread = rev.commentthread_set.latest()
        response = self.client.post(
            reverse('review-detail', args=[self.project.slug, self.review.pk]),
            {'comment': "New Comment!"},
        )
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 3)
        self.assertEqual(thread.comment_set.count(), 1)
        self.assertFalse(
            thread.comment_set.filter(comment='New Comment!').exists()
        )

        new_thread = rev.commentthread_set.latest()
        self.assertTrue(
            new_thread.comment_set.filter(comment='New Comment!').exists()
        )
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.COMMENT_ADDED
            ).count(),
            3
        )

    def test_get_update_comment_view(self):
        response = self.client.get(reverse('update-comment', kwargs={'pk': self.comment.pk}))
        self.assertStatusCode(response, 200)
        self.assertIn('form', response.context)

    def test_update_comment(self):
        response = self.client.post(reverse('update-comment', kwargs={'pk': self.comment.pk}), {
            'comment': 'This is an update'
        })
        self.assertStatusCode(response, 302)
        comment = models.Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.comment, 'This is an update')

    def test_update_comment_with_attachment(self):
        self.assertEqual(self.comment.attachments.count(), 1)
        response = self.client.post(reverse('update-comment', kwargs={'pk': self.comment.pk}), {
            'comment': 'This is an attachment update',
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Comment Edit Description',
            'sort_order': 1,
        })
        self.assertStatusCode(response, 302)
        comment = models.Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.comment, 'This is an attachment update')
        self.assertEqual(self.comment.attachments.count(), 2)
        attachment = self.comment.attachments.latest()
        self.assertEqual(attachment.description, 'Test Comment Edit Description')

    def test_update_comment_with_attachment_without_sort_order(self):
        self.assertEqual(self.comment.attachments.count(), 1)
        response = self.client.post(reverse('update-comment', kwargs={'pk': self.comment.pk}), {
            'comment': 'This is an attachment update',
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Comment Edit Description',
        })
        self.assertStatusCode(response, 200)
        self.assertFormError(response, 'form', 'sort_order',
                             'Attachments require a sort_order')

    def test_delete_comment_attachment(self):
        attachment = self.comment.attachments.get()
        url = reverse('update-comment-attachment', kwargs={
            'comment_pk': self.comment.pk,
            'attachment_pk': attachment.pk
        })
        response = self.client.post(url, {'delete': 'true'})
        self.assertStatusCode(response, 200)
        self.assertTrue(json.loads(response.content.decode('utf-8'))['success'])
        self.assertFalse(
            models.Attachment.objects.filter(pk=attachment.pk).exists()
        )

    def test_delete_comment_attachment_wrong_user(self):
        self.client.logout()
        assert self.client.login(username='test_user_2', password='testing')
        attachment = self.comment.attachments.get()
        url = reverse('update-comment-attachment', kwargs={
            'comment_pk': self.comment.pk,
            'attachment_pk': attachment.pk
        })
        response = self.client.post(url, {'delete': 'true'})
        self.assertStatusCode(response, 404)
        self.assertTrue(
            models.Attachment.objects.filter(pk=attachment.pk).exists()
        )


class TestCommentAPIViews(BaseTestCase):

    def setUp(self):
        super(TestCommentAPIViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        # Sample review
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachment=File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            description='Test Description',
        )
        self.api_url = reverse('comments-api', kwargs={
            'review_pk': self.review.pk,
            'proj_slug': self.review.project.slug,
            'rev_num': self.review.revision.number,
        })
        # Reset out mail queue
        mail.outbox = []

    def test_comment_json_get_review_comments(self):
        response = self.client.get(self.api_url)
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'threads': {
                str(self.comment.thread.pk): [self.comment.to_json()]
            }
        })

    def test_comment_json_get_comment(self):
        response = self.client.get(self.api_url, {'comment_pk': self.comment.pk})
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    def test_comment_json_missing_comment(self):
        response = self.client.get(self.api_url, {'comment_pk': 100000})
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': 'Comment does not exist',
            'comment': {}
        })

    def test_comment_json_create_comment_thread(self):
        response = self.client.post(self.api_url, {
            'comment': "test_comment_json_create_comment_thread",
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Description',
            'sort_order': 1,
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': comment.to_json()
        })
        comment = self.review.revision.commentthread_set.latest().comment_set.get()
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(comment.comment, 'test_comment_json_create_comment_thread')
        self.assertEqual(comment.attachments.count(), 1)

    def test_comment_creation_without_comment(self):
        response = self.client.post(self.api_url, {
            'comment': "",
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Description',
            'sort_order': 1,
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(comment.comment, '')
        self.assertEqual(comment.attachments.count(), 1)

    def test_comment_json_create_comment_error(self):
        response = self.client.post(self.api_url, {})
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': {
                'comment': [
                    'Comment is required if an attachment is not provided'
                ]
            },
            'comment': {}
        })

    def test_comment_json_reply_comment(self):
        thread = self.review.revision.commentthread_set.latest()
        response = self.client.post(self.api_url, {
            'comment': "test_comment_json_reply_comment",
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Description',
            'sort_order': 1,
            'thread': thread.pk
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': comment.to_json()
        })
        self.assertEqual(comment.comment, 'test_comment_json_reply_comment')
        self.assertEqual(comment.thread, thread)
        self.assertEqual(comment.attachments.count(), 1)

    def test_comment_json_reply_invalid_thread(self):
        response = self.client.post(self.api_url, {
            'comment': "Oh nice comment!",
            'description': 'Test Description',
            'thread': 100000000,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': 'Comment Thread 100000000 does not exist',
            'comment': {},
        })

    def test_update_comment_invalid_comment_pk(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': 10000,
            'comment': 'modified comment',
            'delete_attachment': True,
        }))
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': 'Comment 10000 does not exist',
            'comment': {},
        })

    def test_update_comment(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'comment': 'modified comment',
            'delete_attachments': [
                self.comment.attachments.get().pk,
                10000, # We'll just gracefully ignore this delete
            ],
        }))
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 0)
        self.assertEqual(self.comment.comment, 'modified comment')
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    def test_update_comment_without_delete(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'comment': 'modified comment without delete',
        }))
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 1)
        self.assertEqual(self.comment.comment, 'modified comment without delete')
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    def test_update_comment_non_json(self):
        response = self.client.patch(self.api_url, {'test': 'wut'})
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': 'Improperly formed json request',
            'comment': {}
        })
