""" Finite State Machine Controller """
from django.db.models import Q
from django.contrib.auth.models import User

from demotime import constants, models


class State(object):

    def on_enter(self, review, prev_state): # pylint: disable=unused-argument
        review.state = self.name
        review.save(update_fields=['state', 'modified'])

    def on_exit(self, review, next_state):
        """ Stub that children should populate, but is optional. If optional,
        the child should `pass`
        """
        # TODO: Do I even need this on_exit method? I'm not convinced.
        raise NotImplementedError('on_exit not implemented')

    def _common_state_change(self, review, webhook_type=None):
        models.UserReviewStatus.objects.filter(
            review=review
        ).exclude(user=review.creator).update(
            read=False
        )
        if webhook_type:
            review.trigger_webhooks(webhook_type)

    def __eq__(self, other):
        return isinstance(self, type(other))


class Draft(State):

    name = constants.DRAFT

    def on_enter(self, review, prev_state):
        pass

    def on_exit(self, review, next_state):
        pass


class Open(State):

    name = constants.OPEN

    def _open_draft(self, review):
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_CREATED,
            review,
            review.creator
        )
        models.UserReviewStatus.create_user_review_status(
            review, review.creator, True
        )
        review.send_revision_messages()
        models.Reminder.create_reminders_for_review(review)

    def _reopen(self, review, prev_state):
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_OPENED,
            review,
            review.creator
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            models.Message.send_system_message(
                '"{}" has been Reopened'.format(review.title),
                'demotime/messages/reopened.html',
                {
                    'is_reviewer': is_reviewer,
                    'review': review,
                    'previous_state': prev_state.title(),
                    'user': user
                },
                user,
                revision=review.revision,
            )

        models.Reminder.update_reminder_activity_for_review(review, True)

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        if prev_state.name == constants.DRAFT:
            self._open_draft(review)
            webhook_type = constants.CREATED
        elif prev_state.name in (constants.CLOSED, constants.ABORTED):
            self._reopen(review, prev_state.name)
            webhook_type = constants.REOPENED

        self._common_state_change(review, webhook_type)

    def on_exit(self, review, next_state):
        pass


class Closed(State):

    name = constants.CLOSED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_CLOSED,
            review,
            review.creator,
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            models.Message.send_system_message(
                '"{}" has been Closed'.format(review.title),
                'demotime/messages/closed.html',
                {
                    'is_reviewer': is_reviewer,
                    'review': review,
                    'previous_state': prev_state.name.title(),
                    'user': user,
                },
                user,
                revision=review.revision,
            )

        models.Reminder.update_reminder_activity_for_review(review)
        self._common_state_change(review, self.name)

    def on_exit(self, review, next_state):
        pass


class Aborted(State):

    name = constants.ABORTED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_ABORTED,
            review,
            review.creator,
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            models.Message.send_system_message(
                '"{}" has been Aborted'.format(review.title),
                'demotime/messages/closed.html',
                {
                    'is_reviewer': is_reviewer,
                    'review': review,
                    'previous_state': prev_state.name.title(),
                    'user': user,
                },
                user,
                revision=review.revision,
            )

        models.Reminder.update_reminder_activity_for_review(review)
        self._common_state_change(review, self.name)

    def on_exit(self, review, next_state):
        pass


class Cancelled(State):

    name = constants.CANCELLED

    def on_enter(self, review, prev_state):
        pass

    def on_exit(self, review, next_state):
        pass


class StateMachine(object):

    STATE_FIELD = 'state'
    STATE_MAP = {}

    def __init__(self, review):
        self.review = review
        self.state = self._get_state(
            getattr(self.review, self.STATE_FIELD)
        )
        self.previous_state = None

    def _get_state(self, state_str):
        state_cls = self.STATE_MAP[state_str]
        return state_cls()

    def change_state(self, new_state):
        new_state_cls = self.STATE_MAP[new_state]
        new_state = new_state_cls()
        if self.state != new_state:
            self.state.on_exit(self.review, new_state)
            new_state.on_enter(self.review, self.state)
            self.previous_state = self.state
            self.state = new_state
            return True
        else:
            return False

class DemoMachine(StateMachine):

    STATE_MAP = {
        constants.DRAFT: Draft,
        constants.OPEN: Open,
        constants.CLOSED: Closed,
        constants.ABORTED: Aborted,
        constants.CANCELLED: Cancelled,
    }


class Reviewing(State):

    name = constants.REVIEWING

    def on_enter(self, review, prev_state):
        pass

    def on_exit(self, review, next_state):
        pass


class Approved(State):

    name = constants.APPROVED

    def on_enter(self, review, prev_state):
        pass

    def on_exit(self, review, next_state):
        pass


class Rejected(State):

    name = constants.REJECTED

    def on_enter(self, review, prev_state):
        pass

    def on_exit(self, review, next_state):
        pass


class ReviewerMachine(StateMachine):

    STATE_MAP = {
        constants.REVIEWING: Reviewing,
        constants.APPROVED: Approved,
        constants.REJECTED: Rejected,
    }
    STATE_FIELD = 'reviewer_state'
