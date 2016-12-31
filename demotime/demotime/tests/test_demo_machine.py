from mock import patch, Mock

from django.core import mail
#from django.contrib.auth.models import User

from demotime import constants, demo_machine, models
from demotime.tests import BaseTestCase


class BaseDemoMachineCase(BaseTestCase):

    def setUp(self):
        super(BaseDemoMachineCase, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.hook_patch = patch('demotime.models.reviews.Review.trigger_webhooks')
        self.hook_patch_run = self.hook_patch.start()
        self.addCleanup(self.hook_patch.stop)

class TestState(BaseDemoMachineCase):

    def setUp(self):
        super(TestState, self).setUp()
        self.state = demo_machine.State()
        self.state.name = 'default'

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


class TestReviewerState(BaseDemoMachineCase):

    def setUp(self):
        super(TestReviewerState, self).setUp()
        self.state = demo_machine.ReviewerState()
        self.state.name = 'default'

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


class TestDraftState(BaseDemoMachineCase):

    def setUp(self):
        super(TestDraftState, self).setUp()
        self.state = demo_machine.Draft()

    def test_name(self):
        self.assertEqual(self.state.name, constants.DRAFT)

    def test_on_enter(self):
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])

        self.state.on_enter(self.review, demo_machine.Open())
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.DRAFT)
        self.hook_patch_run.assert_not_called()


class TestOpenState(BaseDemoMachineCase):

    def setUp(self):
        super(TestOpenState, self).setUp()
        self.state = demo_machine.Open()

    def test_name(self):
        self.assertEqual(self.state.name, constants.OPEN)

    def test_open_draft(self):
        models.Event.objects.all().delete()
        models.Message.objects.all().delete()
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).delete()
        models.Reminder.objects.all().delete()
        mail.outbox = []

        self.state._open_draft(self.review) # pylint: disable=protected-access
        event = models.Event.objects.get(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertEqual(event.event_type.code, models.EventType.DEMO_CREATED)
        self.assertEqual(
            event.user,
            self.review.creator_set.active().get().user
        )

        # reviewer events
        reviewer_events = models.Event.objects.filter(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(reviewer_events.count(), 3)

        # follower events
        follower_events = models.Event.objects.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertEqual(follower_events.count(), 2)

        statuses = models.UserReviewStatus.objects.filter(review=self.review)
        # We just make the creator's here
        self.assertEqual(statuses.count(), 1)
        self.assertEqual(
            statuses.get().user,
            self.review.creator_set.active().get().user
        )

        reminders = models.Reminder.objects.filter(review=self.review)
        # 3 reviewers, 1 creator
        self.assertEqual(reminders.count(), 4)

        messages = models.Message.objects.all()
        # 2 followers, 3 reviewers
        self.assertEqual(messages.count(), 5)
        self.assertEqual(len(mail.outbox), 5)

    def test_reopen(self):
        models.Event.objects.all().delete()
        models.Message.objects.all().delete()
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).delete()
        models.Reminder.objects.all().update(active=False)
        mail.outbox = []
        self.review.state = constants.CLOSED
        self.review.reviewer_state = constants.APPROVED
        self.review.save(update_fields=['state', 'reviewer_state'])

        self.state._reopen(self.review, 'PREVIOUS') # pylint: disable=protected-access
        self.review.refresh_from_db()
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_OPENED)
        self.assertEqual(
            event.user,
            self.review.creator_set.active().get().user
        )
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)
        for reviewer in self.review.reviewer_set.active():
            self.assertEqual(reviewer.status, constants.REVIEWING)

        reminders = models.Reminder.objects.filter(
            review=self.review, active=True
        )
        # 3 reviewers, 1 creator
        self.assertEqual(reminders.count(), 4)

        messages = models.Message.objects.all()
        # 2 followers, 3 reviewers
        self.assertEqual(messages.count(), 5)
        self.assertEqual(len(mail.outbox), 5)

    def test_on_enter_draft(self):
        # pylint: disable=protected-access
        self.state._open_draft = Mock()
        self.state._common_state_change = Mock()
        previous_state = demo_machine.Draft()

        self.state.on_enter(self.review, previous_state)
        self.state._open_draft.assert_called_once_with(self.review)
        self.state._common_state_change.assert_called_once_with(
            self.review, constants.CREATED
        )

    def test_on_enter_reopen_closed(self):
        # pylint: disable=protected-access
        self.state._reopen = Mock()
        self.state._common_state_change = Mock()
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        previous_state = demo_machine.Closed()

        self.state.on_enter(self.review, previous_state)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.OPEN)
        self.state._reopen.assert_called_once_with(
            self.review, previous_state.name)
        self.state._common_state_change.assert_called_once_with(
            self.review, constants.REOPENED
        )

    def test_on_enter_reopen_aborted(self):
        # pylint: disable=protected-access
        self.state._reopen = Mock()
        self.state._common_state_change = Mock()
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        previous_state = demo_machine.Aborted()

        self.state.on_enter(self.review, previous_state)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.OPEN)
        self.state._reopen.assert_called_once_with(
            self.review, previous_state.name)
        self.state._common_state_change.assert_called_once_with(
            self.review, constants.REOPENED
        )

    def test_on_enter_reopen_paused(self):
        # pylint: disable=protected-access
        self.state._reopen = Mock()
        self.state._common_state_change = Mock()
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        previous_state = demo_machine.Paused()

        self.state.on_enter(self.review, previous_state)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.OPEN)
        self.state._reopen.assert_called_once_with(
            self.review, previous_state.name)
        self.state._common_state_change.assert_called_once_with(
            self.review, constants.REOPENED
        )


class TestPausedState(BaseDemoMachineCase):

    def setUp(self):
        super(TestPausedState, self).setUp()
        self.state = demo_machine.Paused()

    def test_name(self):
        self.assertEqual(self.state.name, constants.PAUSED)

    def test_on_enter(self):
        models.Event.objects.all().delete()
        models.Message.objects.all().delete()
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).delete()
        models.Reminder.objects.all().update(active=True)
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Open())
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.PAUSED)
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_PAUSED)
        self.assertEqual(
            event.user,
            self.review.creator_set.active().get().user
        )

        reminders = models.Reminder.objects.filter(
            review=self.review, active=False
        )
        # 3 reviewers, 1 creator
        self.assertEqual(reminders.count(), 4)

        messages = models.Message.objects.filter(
            title__contains='Paused',
            review=self.review.revision
        )
        # 2 followers, 3 reviewers
        self.assertEqual(messages.count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.hook_patch_run.assert_called_once_with(
            constants.PAUSED
        )


class TestClosedState(BaseDemoMachineCase):

    def setUp(self):
        super(TestClosedState, self).setUp()
        self.state = demo_machine.Closed()

    def test_name(self):
        self.assertEqual(self.state.name, constants.CLOSED)

    def test_on_enter(self):
        models.Event.objects.all().delete()
        models.Message.objects.all().delete()
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).delete()
        models.Reminder.objects.all().update(active=True)
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Open())
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.CLOSED)
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_CLOSED)
        self.assertEqual(
            event.user,
            self.review.creator_set.active().get().user
        )

        reminders = models.Reminder.objects.filter(
            review=self.review, active=False
        )
        # 3 reviewers, 1 creator
        self.assertEqual(reminders.count(), 4)

        messages = models.Message.objects.filter(
            title__contains='Closed',
            review=self.review.revision
        )
        # 2 followers, 3 reviewers
        self.assertEqual(messages.count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.hook_patch_run.assert_called_once_with(
            constants.CLOSED
        )


class TestAbortedState(BaseDemoMachineCase):

    def setUp(self):
        super(TestAbortedState, self).setUp()
        self.state = demo_machine.Aborted()

    def test_name(self):
        self.assertEqual(self.state.name, constants.ABORTED)

    def test_on_enter(self):
        models.Event.objects.all().delete()
        models.Message.objects.all().delete()
        models.UserReviewStatus.objects.filter(
            review=self.review
        ).delete()
        models.Reminder.objects.all().update(active=True)
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Open())
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.ABORTED)
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_ABORTED)
        self.assertEqual(
            event.user,
            self.review.creator_set.active().get().user
        )

        reminders = models.Reminder.objects.filter(
            review=self.review, active=False
        )
        # 3 reviewers, 1 creator
        self.assertEqual(reminders.count(), 4)

        messages = models.Message.objects.filter(
            title__contains='Aborted',
            review=self.review.revision
        )
        # 2 followers, 3 reviewers
        self.assertEqual(messages.count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.hook_patch_run.assert_called_once_with(
            constants.ABORTED
        )


class TestCancelledState(BaseDemoMachineCase):

    def setUp(self):
        super(TestCancelledState, self).setUp()
        self.state = demo_machine.Cancelled()

    def test_name(self):
        self.assertEqual(self.state.name, constants.CANCELLED)

    def test_on_enter(self):
        self.review.state = 'notastate'
        self.review.save(update_fields=['state'])

        self.state.on_enter(self.review, demo_machine.Draft())
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, constants.CANCELLED)
        self.hook_patch_run.assert_not_called()


class TestReviewingState(BaseDemoMachineCase):

    def setUp(self):
        super(TestReviewingState, self).setUp()
        self.state = demo_machine.Reviewing()

    def test_name(self):
        self.assertEqual(self.state.name, constants.REVIEWING)

    def test_on_enter(self):
        self.review.reviewer_state = 'notastate'
        self.review.save(update_fields=['reviewer_state'])
        models.Message.objects.all().delete()
        models.Event.objects.all().delete()
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Approved())
        self.review.refresh_from_db()
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)

        self.assertEqual(
            models.Message.objects.filter(
                title__contains='Under Review',
                review=self.review.revision
            ).count(),
            1
        )
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_REVIEWING)
        self.hook_patch_run.assert_called_once_with(
            constants.REVIEWING
        )


class TestApprovedState(BaseDemoMachineCase):

    def setUp(self):
        super(TestApprovedState, self).setUp()
        self.state = demo_machine.Approved()

    def test_on_enter(self):
        self.review.reviewer_state = 'notastate'
        self.review.save(update_fields=['reviewer_state'])
        models.Message.objects.all().delete()
        models.Event.objects.all().delete()
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Reviewing())
        self.review.refresh_from_db()
        self.assertEqual(self.review.reviewer_state, constants.APPROVED)

        self.assertEqual(
            models.Message.objects.filter(
                title__contains='Approved',
                review=self.review.revision
            ).count(),
            1
        )
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_APPROVED)
        self.hook_patch_run.assert_called_once_with(
            constants.APPROVED
        )


class TestRejectedState(BaseDemoMachineCase):

    def setUp(self):
        super(TestRejectedState, self).setUp()
        self.state = demo_machine.Rejected()

    def test_on_enter(self):
        self.review.reviewer_state = 'notastate'
        self.review.save(update_fields=['reviewer_state'])
        models.Message.objects.all().delete()
        models.Event.objects.all().delete()
        mail.outbox = []

        self.state.on_enter(self.review, demo_machine.Reviewing())
        self.review.refresh_from_db()
        self.assertEqual(self.review.reviewer_state, constants.REJECTED)

        self.assertEqual(
            models.Message.objects.filter(
                title__contains='Rejected',
                review=self.review.revision
            ).count(),
            1
        )
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.DEMO_REJECTED)
        self.hook_patch_run.assert_called_once_with(
            constants.REJECTED
        )


class TestDemoMachine(BaseDemoMachineCase):

    def setUp(self):
        super(TestDemoMachine, self).setUp()
        self.machine = demo_machine.DemoMachine(self.review)

    def test_init(self):
        self.assertEqual(self.machine.review, self.review)
        self.assertEqual(self.machine.state, demo_machine.Open())
        self.assertEqual(self.machine.previous_state, None)

    def test_get_state(self):
        # pylint: disable=protected-access
        state = self.machine._get_state(constants.CLOSED)
        self.assertEqual(state, demo_machine.Closed())

    def test_change_state_new_state(self):
        self.assertTrue(self.machine.change_state(constants.CLOSED))
        self.review.refresh_from_db()
        self.assertEqual(self.machine.previous_state, demo_machine.Open())
        self.assertEqual(self.machine.state, demo_machine.Closed())
        self.assertEqual(self.review.state, constants.CLOSED)

    def test_change_state_same_state(self):
        self.assertFalse(self.machine.change_state(constants.OPEN))
        self.review.refresh_from_db()
        self.assertEqual(self.machine.previous_state, None)
        self.assertEqual(self.machine.state, demo_machine.Open())
        self.assertEqual(self.review.state, constants.OPEN)

    def test_change_state_invalid_state(self):
        with self.assertRaises(KeyError):
            self.machine.change_state('NOT REAL')


class TestReviewerMachine(BaseDemoMachineCase):

    def setUp(self):
        super(TestReviewerMachine, self).setUp()
        self.machine = demo_machine.ReviewerMachine(self.review)

    def test_init(self):
        self.assertEqual(self.machine.review, self.review)
        self.assertEqual(self.machine.state, demo_machine.Reviewing())
        self.assertEqual(self.machine.previous_state, None)

    def test_get_state(self):
        # pylint: disable=protected-access
        state = self.machine._get_state(constants.APPROVED)
        self.assertEqual(state, demo_machine.Approved())

    def test_change_state_new_state(self):
        self.assertTrue(self.machine.change_state(constants.APPROVED))
        self.review.refresh_from_db()
        self.assertEqual(self.machine.previous_state, demo_machine.Reviewing())
        self.assertEqual(self.machine.state, demo_machine.Approved())
        self.assertEqual(self.review.reviewer_state, constants.APPROVED)

    def test_change_state_same_state(self):
        self.assertFalse(self.machine.change_state(constants.REVIEWING))
        self.review.refresh_from_db()
        self.assertEqual(self.machine.previous_state, None)
        self.assertEqual(self.machine.state, demo_machine.Reviewing())
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)

    def test_change_state_invalid_state(self):
        with self.assertRaises(KeyError):
            self.machine.change_state('NOT REAL')
