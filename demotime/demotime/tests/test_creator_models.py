from mock import patch

from django.core import mail

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestCreatorModels(BaseTestCase):

    def setUp(self):
        super(TestCreatorModels, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        mail.outbox = []

    def test_create_creator_no_notify(self):
        assert False

    def test_create_creator_no_notify_inactive(self):
        assert False

    def test_create_creator_notify(self):
        assert False

    def test_create_creator_event_added(self):
        assert False

    def test_create_creator_event_removed(self):
        assert False

    def test_drop_creator(self):
        assert False

    def test_create_too_many_creators(self):
        assert False

    def test_create_dupe_creators(self):
        assert False

    def test_to_json(self):
        assert False
