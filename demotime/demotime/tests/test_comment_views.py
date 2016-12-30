import json

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
        self.review = models.Review.create_review(**self.default_review_kwargs)
        attachments = [{
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Description',
        }]
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachments=attachments,
        )
        # Reset out mail queue
        mail.outbox = []

    # TODO: Attachments API - Move these tests to go with that, y'know, when
    # you actually do that someday.
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
        attachments = [{
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'description': 'Test Description',
        }]
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachments=attachments,
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
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Test Description',
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

    def test_comment_json_create_comment_thread_issue(self):
        response = self.client.post(self.api_url, {
            'comment': "test_comment_json_create_comment_thread",
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Test Description',
            'is_issue': True,
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertIsNotNone(comment.issue())
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
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Test Description',
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(comment.comment, '')
        self.assertEqual(comment.attachments.count(), 1)

    def test_comment_with_multiple_attachments(self):
        response = self.client.post(self.api_url, {
            'comment': 'Test comment with multiple attachments',
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Image Attachment',
            '1-attachment': File(BytesIO(b'test_file_2'), name='test_file_2.mov'),
            '1-description': 'Movie Attachment',
            '2-attachment': File(BytesIO(b'test_file_3'), name='test_file_3.wav'),
            '2-description': 'Audio Attachment',
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertTrue(comment.events.filter(
            event_type__code=models.EventType.COMMENT_ADDED
        ).exists())
        self.assertEqual(
            comment.comment,
            'Test comment with multiple attachments'
        )
        self.assertEqual(comment.attachments.count(), 3)
        attachment_one, attachment_two, attachment_three = comment.attachments.all().order_by('sort_order')
        # One
        self.assertEqual(attachment_one.attachment.file.read(), b'test_file_1')
        self.assertEqual(attachment_one.attachment_type, 'image')
        self.assertEqual(attachment_one.description, 'Image Attachment')
        self.assertEqual(attachment_one.sort_order, 0)

        # Two
        self.assertEqual(attachment_two.attachment.file.read(), b'test_file_2')
        self.assertEqual(attachment_two.attachment_type, 'movie')
        self.assertEqual(attachment_two.description, 'Movie Attachment')
        self.assertEqual(attachment_two.sort_order, 1)

        # Three
        self.assertEqual(attachment_three.attachment.file.read(), b'test_file_3')
        self.assertEqual(attachment_three.attachment_type, 'audio')
        self.assertEqual(attachment_three.description, 'Audio Attachment')
        self.assertEqual(attachment_three.sort_order, 2)

    def test_comment_json_create_comment_error(self):
        response = self.client.post(self.api_url, {})
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'failure',
            'errors': {
                'comment': ['This field is required.']
            },
            'comment': {}
        })

    def test_comment_json_reply_comment(self):
        thread = self.review.revision.commentthread_set.latest()
        response = self.client.post(self.api_url, {
            'comment': "test_comment_json_reply_comment",
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Test Description',
            '0-sort_order': 1,
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

    def test_comment_json_reply_comment_as_issue(self):
        thread = self.review.revision.commentthread_set.latest()
        response = self.client.post(self.api_url, {
            'comment': "test_comment_json_reply_comment",
            '0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            '0-description': 'Test Description',
            '0-sort_order': 1,
            'thread': thread.pk,
            'is_issue': True
        })
        self.assertStatusCode(response, 200)
        comment = models.Comment.objects.latest('created')
        self.assertIsNotNone(comment.issue())
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

    def test_mark_comment_as_issue(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'issue': {'create': True}
        }))
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 1)
        self.assertEqual(self.comment.comment, 'Test Comment')
        self.assertIsNotNone(self.comment.issue())
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    def test_resolve_issue(self):
        models.Issue.create_issue(
            self.review, self.comment, self.user
        )
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'issue': {'resolve': True}
        }))
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 1)
        self.assertEqual(self.comment.comment, 'Test Comment')
        self.assertIsNone(self.comment.issue())
        issue = models.Issue.objects.get()
        self.assertEqual(issue.resolved_by, self.user)
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    def test_create_and_resolve_issue_failure(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'issue': {'create': True, 'resolve': True}
        }))
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'errors': "Can't both create and resolve an issue",
            'status': 'failure',
            'comment': self.comment.to_json()
        })

    def test_create_issue_existing_issue(self):
        models.Issue.create_issue(
            self.review, self.comment, self.user
        )
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'issue': {'create': True}
        }))
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'errors': 'Issue already exists for Comment {}'.format(
                self.comment.pk
            ),
            'status': 'failure',
            'comment': {},
        })

    def test_resolve_missing_issue(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'issue': {'resolve': True}
        }))
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'errors': 'Can not resolve an issue that does not exist',
            'status': 'failure',
            'comment': {},
        })

    def test_update_comment_delete_attachment(self):
        response = self.client.patch(self.api_url, json.dumps({
            'comment_pk': self.comment.pk,
            'delete_attachments': [
                self.comment.attachments.get().pk,
                10000, # We'll just gracefully ignore this delete
            ],
        }))
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 0)
        self.assertEqual(self.comment.comment, 'Test Comment')
        self.assertEqual(json.loads(response.content.decode('utf8')), {
            'status': 'success',
            'errors': '',
            'comment': self.comment.to_json()
        })

    """
    Not quite sure how to make this patch request with multiple files work with
    the Django test client. Going to see if we can get it working in a browser
    and then reassess. Maybe this is just the wrong way to do this. Maybe an
    Attachment API makes more sense?
    def test_update_comment_with_multiple_files(self):
        self.comment.attachments.all().delete()
        self.assertFalse(self.comment.attachments.exists())
        response = self.client.patch(
            self.api_url,
            data={
                'data': json.dumps({
                    'comment_pk': self.comment.pk,
                    'comment': 'multiple attachments',
                    '0-attachment_type': 'image',
                    '0-description': 'image attachment',
                    '1-attachment_type': 'movie',
                    '1-description': 'movie attachment',
                }),
                'files': {
                    '0-attachment': File(BytesIO(b'test_file_1')),
                    '1-attachment': File(BytesIO(b'test_file_2')),
                }
            },
            content_type='multipart/form-data',
        )
        self.assertStatusCode(response, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.attachments.count(), 2)
    """

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
