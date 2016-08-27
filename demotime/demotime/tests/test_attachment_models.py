from demotime import models
from demotime.tests import BaseTestCase


class TestAttachmentModel(BaseTestCase):

    def setUp(self):
        super(TestAttachmentModel, self).setUp()
        # Sample review
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.attachment = models.Attachment.objects.first()

    def test_attachment_to_json(self):
        self.assertEqual(self.attachment._to_json(), {
            'static_url': '/file/1',
            'attachment_type': models.Attachment.IMAGE,
            'description': 'Testing'
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
