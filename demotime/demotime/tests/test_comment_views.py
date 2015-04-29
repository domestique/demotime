import json
from StringIO import StringIO

from django.core import mail
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import models
from demotime.tests import BaseTestCase


class TestCommentViews(BaseTestCase):

    def setUp(self):
        super(TestCommentViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        # Sample review
        self.review = models.Review.create_review(
            creator=self.user,
            title='Test Title',
            description='Test Description',
            case_link='http://example.org/',
            reviewers=self.test_users,
            attachments=[
                {
                    'attachment': File(BytesIO('test_file_1')),
                    'attachment_type': 'photo',
                    'description': 'Testing',
                },
                {
                    'attachment': File(BytesIO('test_file_2')),
                    'attachment_type': 'photo',
                    'description': 'Testing',
                },
            ],
        )
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachment=File(BytesIO('test_file_1')),
            attachment_type='photo',
            description='Test Description',
        )
        # Reset out mail queue
        mail.outbox = []

    def test_comment_on_review(self):
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
            'attachment': fh,
            'attachment_type': 'photo',
            'description': 'Test Description',
        })
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
        self.assertEqual(attachment.attachment_type, models.Attachment.PHOTO)
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            6
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        self.assertEqual(len(mail.outbox), 3)

    def test_reply_to_comment(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
        })
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(len(mail.outbox), 3)

        thread = rev.commentthread_set.latest()
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Reply!",
            'thread': thread.pk
        })
        self.assertStatusCode(response, 302)
        # Still just 1 thread
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(thread.comment_set.count(), 2)
        self.assertTrue(thread.comment_set.filter(comment='Reply!').exists())
        self.assertEqual(len(mail.outbox), 6)

    def test_create_second_thread(self):
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
        })
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 2)

        thread = rev.commentthread_set.latest()
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "New Comment!",
        })
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
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        self.assertEqual(self.comment.attachments.count(), 1)
        response = self.client.post(reverse('update-comment', kwargs={'pk': self.comment.pk}), {
            'comment': 'This is an attachment update',
            'attachment': fh,
            'attachment_type': 'photo',
            'description': 'Test Comment Edit Description',
        })
        self.assertStatusCode(response, 302)
        comment = models.Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.comment, 'This is an attachment update')
        self.assertEqual(self.comment.attachments.count(), 2)
        attachment = self.comment.attachments.latest()
        self.assertEqual(attachment.description, 'Test Comment Edit Description')

    def test_delete_comment_attachment(self):
        attachment = self.comment.attachments.get()
        url = reverse('update-comment-attachment', kwargs={
            'comment_pk': self.comment.pk,
            'attachment_pk': attachment.pk
        })
        response = self.client.post(url, {'delete': 'true'})
        self.assertStatusCode(response, 200)
        self.assertTrue(json.loads(response.content)['success'])
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
