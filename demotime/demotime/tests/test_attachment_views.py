import json

from django.core import mail
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestAttachmentViews(BaseTestCase):

    def setUp(self):
        super(TestAttachmentViews, self).setUp()
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
        self.attachment = self.comment.attachments.all()[0]
        self.create_url = reverse('attachments-api', kwargs={
            'review_pk': self.review.pk
        })
        self.attach_url = reverse('attachments-api', kwargs={
            'review_pk': self.review.pk, 'attachment_pk': self.attachment.pk
        })
        # Reset our mail queue
        mail.outbox = []

    def test_create_attachment(self):
        models.Attachment.objects.all().delete()
        response = self.client.post(self.create_url, {
            'object_type': constants.REVIEW,
            'object_pk': self.review.pk,
            'files': [
                File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                File(BytesIO(b'test_file_2'), name='test_file_2.png'),
            ],
        })
        self.assertStatusCode(response, 201)
        attachments = []
        for attachment in self.review.revision.attachments.all():
            attachments.append(attachment.to_json())
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'success',
            'errors': [],
            'attachments': attachments
        })

    def test_create_attachment_on_comment(self):
        models.Attachment.objects.all().delete()
        response = self.client.post(self.create_url, {
            'object_type': constants.COMMENT,
            'object_pk': self.comment.pk,
            'files': [
                File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                File(BytesIO(b'test_file_2'), name='test_file_2.png'),
            ],
        })
        self.assertStatusCode(response, 201)
        attachments = []
        for attachment in self.comment.attachments.all():
            attachments.append(attachment.to_json())
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'success',
            'errors': [],
            'attachments': attachments
        })

    def test_create_attachment_attachment_url(self):
        response = self.client.post(self.attach_url, {
            'object_type': constants.REVIEW,
            'object_pk': self.review.pk,
            'files': [
                File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                File(BytesIO(b'test_file_2'), name='test_file_2.png'),
            ],
        })
        self.assertStatusCode(response, 400)

    def test_create_attachment_generic_errors(self):
        response = self.client.post(self.create_url, {})
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'failure',
            'errors': {
                'object_pk': ['This field is required.'],
                'object_type': ['This field is required.'],
            },
        })

    def test_create_attachment_missing_object(self):
        response = self.client.post(self.create_url, {
            'object_type': constants.REVIEW,
            'object_pk': 10000,
            'files': [
                File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                File(BytesIO(b'test_file_2'), name='test_file_2.png'),
            ],
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'failure',
            'errors': {'__all__': ['Invalid object provided for attachment']},
        })

    def test_create_attachment_missing_files(self):
        response = self.client.post(self.create_url, {
            'object_type': constants.REVIEW,
            'object_pk': self.review.pk,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'failure',
            'errors': {'files': ['No files provided for attaching']},
        })

    def test_get_attachment(self):
        response = self.client.get(self.attach_url)
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'success',
            'errors': [],
            'attachment': self.attachment.to_json()
        })

    def test_delete_attachment(self):
        response = self.client.delete(self.attach_url)
        self.assertStatusCode(response, 204)
        self.assertFalse(
            models.Attachment.objects.filter(pk=self.attachment.pk).exists()
        )
