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

    def test_setting_value_emojis(self):
        template = Template(
            "{% load demo_tags %}{% setting_value project 'emojis_enabled' as emojis_enabled %}"
            "{% if emojis_enabled == True %}True{% else %}False{% endif %}"
        )
        content = template.render(Context({'project': self.project}))
        self.assertEqual(content, 'True')

    def test_setting_value_boolean(self):
        # Note, 'True' not True. Should return 'False'
        template = Template(
            "{% load demo_tags %}{% setting_value project 'emojis_enabled' as emojis_enabled %}"
            "{% if emojis_enabled == 'True' %}True{% else %}False{% endif %}"
        )
        content = template.render(Context({'project': self.project}))
        self.assertEqual(content, 'False')

    def test_setting_value_missing_project(self):
        template = Template(
            "{% load demo_tags %}{% setting_value project 'emojis_enabled' %}"
        )
        with self.assertRaises(TypeError):
            template.render(Context({'project': None}))

    def test_creator_for_user(self):
        request = Mock()
        request.user = self.review.creator_set.active().get().user
        template = Template(
            "{% load demo_tags %}{% creator_for_user review.pk as creator %}{{ creator.review.pk }}"
        )
        content = template.render(Context(
            {'request': request, 'review': self.review}
        ))
        self.assertEqual(content, str(self.review.pk))

    def test_creator_for_user_not_creator(self):
        request = Mock()
        request.user = self.user
        template = Template(
            "{% load demo_tags %}{% creator_for_user review.pk as creator %}{{ creator.review.pk }}"
        )
        content = template.render(Context(
            {'request': request, 'review': self.review}
        ))
        self.assertEqual(content, '')

    def test_creator_for_user_invalid_pk(self):
        request = Mock()
        request.user = self.review.creator_set.active().get().user
        template = Template(
            "{% load demo_tags %}{% creator_for_user 'foob4r' as creator %}{{ creator.review.pk }}"
        )
        content = template.render(Context(
            {'request': request, 'review': self.review}
        ))
        self.assertEqual(content, '')

    def test_creator_for_user_inactive_creator(self):
        user = User.objects.get(username='test_user')
        models.Creator.objects.filter(
            user=user
        ).update(active=False)
        request = Mock()
        request.user = user
        template = Template(
            "{% load demo_tags %}{% creator_for_user review.pk as creator %}{{ creator.review.pk }}"
        )
        content = template.render(Context(
            {'request': request, 'review': self.review}
        ))
        self.assertEqual(content, '')
