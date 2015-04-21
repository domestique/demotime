from mock import Mock

from django.contrib.auth.models import User
from django.template import Context, Template

from demotime import models
from demotime.templatetags import demo_tags
from demotime.tests import BaseTestCase


class TestDemoTags(BaseTestCase):

    def setUp(self):
        super(TestDemoTags, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.request = Mock()
        self.request.user = User.objects.get(username='test_user_0')

    def test_review_status(self):
        self.assertEqual(
            demo_tags.review_status(self.review, self.request),
            models.reviews.REVIEWING.capitalize()
        )

    def test_review_status_render(self):
        template = Template(
            "{% load demo_tags %}{% review_status review request %}"
        )
        content = template.render(
            Context({'review': self.review, 'request': self.request})
        )
        self.assertEqual(content, models.reviews.REVIEWING.capitalize())
