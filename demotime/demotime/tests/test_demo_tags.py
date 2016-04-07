from django.contrib.auth.models import User
from django.template import Context, Template

from demotime import models
from demotime.templatetags import demo_tags
from demotime.tests import BaseTestCase


class TestDemoTags(BaseTestCase):

    def setUp(self):
        super(TestDemoTags, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Grab our reviewer
        self.user = User.objects.get(username='test_user_0')

    def test_review_status(self):
        self.assertEqual(
            demo_tags.reviewer_status(self.review, self.user),
            models.reviews.REVIEWING.capitalize()
        )

    def test_review_status_render(self):
        template = Template(
            "{% load demo_tags %}{% reviewer_status review user %}"
        )
        content = template.render(
            Context({'review': self.review, 'user': self.user})
        )
        self.assertEqual(content, models.reviews.REVIEWING.capitalize())

    def test_review_status_revision(self):
        template = Template(
            "{% load demo_tags %}{% reviewer_status review.revision user %}"
        )
        content = template.render(
            Context({'review': self.review, 'user': self.user})
        )
        self.assertEqual(content, models.reviews.REVIEWING.capitalize())

    def test_review_status_no_reviewer(self):
        self.review.reviewer_set.filter(reviewer=self.user).delete()
        self.assertEqual(
            demo_tags.reviewer_status(self.review, self.user),
            ''
        )
