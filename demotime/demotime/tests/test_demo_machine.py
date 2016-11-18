from mock import patch

#from django.core import mail
#from django.contrib.auth.models import User

from demotime import constants, demo_machine, models
from demotime.tests import BaseTestCase


class TestState(BaseTestCase):

    def setUp(self):
        super(TestState, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.state = demo_machine.State()
        self.state.name = 'default'
        self.hook_patch = patch('demotime.models.reviews.Review.trigger_webhooks')
        self.hook_patch_run = self.hook_patch.start()
        self.addCleanup(self.hook_patch.stop)

    def test_on_enter(self):
        prev_state = demo_machine.State()
        prev_state.name = 'previous'
        self.state.on_enter(self.review, prev_state)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, self.state.name)

    def test_common_state_change(self):
        status_count = models.UserReviewStatus.objects.filter(
            review=self.review
        ).update(read=True)
        # pylint: disable=protected-access
        self.state._common_state_change(self.review, constants.APPROVED)
        updated_status_count = models.UserReviewStatus.objects.filter(
            review=self.review, read=False
        ).count()
        # Everyone but the creator of the Demo
        self.assertEqual(updated_status_count, status_count - 1)
        self.hook_patch_run.assert_called_once_with(
            constants.APPROVED
        )

    def test_equality(self):
        same_state = demo_machine.State()
        self.assertEqual(self.state, same_state)

    def test_inequality(self):
        class DifferentState(demo_machine.State):
            pass

        diff_state = DifferentState()
        self.assertNotEqual(self.state, diff_state)


class TestReviewerState(BaseTestCase):

    def setUp(self):
        super(TestReviewerState, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.state = demo_machine.ReviewerState()
        self.state.name = 'default'
        self.hook_patch = patch('demotime.models.reviews.Review.trigger_webhooks')
        self.hook_patch_run = self.hook_patch.start()
        self.addCleanup(self.hook_patch.stop)

    def test_on_enter(self):
        prev_state = demo_machine.ReviewerState()
        prev_state.name = 'previous'
        self.state.on_enter(self.review, prev_state)
        self.review.refresh_from_db()
        self.assertEqual(self.review.reviewer_state, self.state.name)

    def test_common_state_change(self):
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).update(read=True)
        # pylint: disable=protected-access
        self.state._common_state_change(self.review, constants.APPROVED)
        updated_status_count = models.UserReviewStatus.objects.filter(
            review=self.review, read=False
        ).count()
        # Just the Demo Creator
        self.assertEqual(updated_status_count, 1)
        self.hook_patch_run.assert_called_once_with(
            constants.APPROVED
        )
