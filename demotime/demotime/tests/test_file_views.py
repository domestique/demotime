import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from demotime import models
from demotime.tests import BaseTestCase


TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


class TestFileViews(BaseTestCase):

    def setUp(self):
        super(TestFileViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.attachment = self.review.revision.attachments.all()[0]

    def test_user_can_view_media(self):
        response = self.client.get(
            reverse('user-media', args=[self.attachment.pk])
        )
        self.assertStatusCode(response, 200)

    def test_user_can_not_view_media(self):
        models.ProjectMember.objects.all().delete()
        models.ProjectGroup.objects.all().delete()
        response = self.client.get(
            reverse('user-media', args=[self.attachment.pk])
        )
        self.assertStatusCode(response, 403)
