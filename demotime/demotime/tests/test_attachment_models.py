from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestAttachmentModel(BaseTestCase):

    def setUp(self):
        super(TestAttachmentModel, self).setUp()
        # Sample review
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.attachment = models.Attachment.objects.first()

    def test_determine_attachment_type_image(self):
        filename_str = 'test_file.{}'
        suffixes = constants.ATTACHMENT_MAP[constants.IMAGE]
        for suffix in suffixes:
            self.assertEqual(
                models.attachments.determine_attachment_type(
                    filename_str.format(suffix)
                ),
                constants.IMAGE
            )

    def test_determine_attachment_type_movie(self):
        filename_str = 'test_file.{}'
        suffixes = constants.ATTACHMENT_MAP[constants.MOVIE]
        for suffix in suffixes:
            self.assertEqual(
                models.attachments.determine_attachment_type(
                    filename_str.format(suffix)
                ),
                constants.MOVIE
            )

    def test_determine_attachment_type_audio(self):
        filename_str = 'test_file.{}'
        suffixes = constants.ATTACHMENT_MAP[constants.AUDIO]
        for suffix in suffixes:
            self.assertEqual(
                models.attachments.determine_attachment_type(
                    filename_str.format(suffix)
                ),
                constants.AUDIO
            )

    def test_determine_attachment_type_doc(self):
        filename_str = 'test_file.{}'
        suffixes = constants.ATTACHMENT_MAP[constants.DOCUMENT]
        for suffix in suffixes:
            self.assertEqual(
                models.attachments.determine_attachment_type(
                    filename_str.format(suffix)
                ),
                constants.DOCUMENT
            )

    def test_determine_attachment_type_other(self):
        filename_str = 'test_file.{}'
        suffixes = ('wut', 'bashrc', 'ini')
        for suffix in suffixes:
            self.assertEqual(
                models.attachments.determine_attachment_type(
                    filename_str.format(suffix)
                ),
                constants.OTHER
            )

    def test_create_attachment(self):
        attachment = models.Attachment.create_attachment(
            attachment=File(BytesIO(b'test_file_1'), name='test_file_1.mov'),
            description='Create Attachment',
            sort_order=5,
            content_object=self.review,
        )
        self.assertEqual(attachment.description, 'Create Attachment')
        self.assertEqual(attachment.attachment_type, constants.MOVIE)
        self.assertEqual(attachment.sort_order, 5)
        self.assertEqual(attachment.content_object, self.review)

    def test_attachment_to_json(self):
        self.assertEqual(self.attachment.to_json(), {
            'static_url': '/file/{}'.format(self.attachment.pk),
            'attachment_type': constants.IMAGE,
            'description': 'Testing',
            'created': self.attachment.created.isoformat(),
            'modified': self.attachment.modified.isoformat(),
        })

    def test_pretty_name(self):
        self.assertEqual(
            self.attachment.pretty_name,
            self.attachment.attachment.name.split('/')[-1]
        )

    def test_review_property(self):
        self.assertEqual(self.attachment.review, self.review)

    def test_project_property(self):
        self.assertEqual(self.attachment.project, self.review.project)
