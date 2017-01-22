""" Finite State Machine Controller """
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from demotime import constants, helpers, models


class State(object):

    def on_enter(self, review, prev_state): # pylint: disable=unused-argument
        review.state = self.name
        review.save(update_fields=['state', 'modified'])

    def _common_state_change(self, review, webhook_type=None):
        models.UserReviewStatus.objects.filter(
            review=review
        ).exclude(user=review.last_action_by).update(
            read=False
        )
        if webhook_type:
            review.trigger_webhooks(webhook_type)

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__


class ReviewerState(State):

    def on_enter(self, review, prev_state): # pylint: disable=unused-argument
        review.reviewer_state = self.name
        review.save(update_fields=['reviewer_state', 'modified'])

    def _common_state_change(self, review, webhook_type=None):
        models.UserReviewStatus.objects.filter(
            review=review,
            user=review.last_action_by,
        ).update(
            read=False
        )
        if webhook_type:
            review.trigger_webhooks(webhook_type)


class Draft(State):

    name = constants.DRAFT


class Open(State):

    name = constants.OPEN

    def _open_draft(self, review):
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_CREATED,
            review,
            review.last_action_by
        )
        models.UserReviewStatus.create_user_review_status(
            review, review.last_action_by, True
        )
        review.send_revision_messages()
        models.Reminder.create_reminders_for_review(review)
        review.created = timezone.now()
        review.save(update_fields=['created', 'modified'])
        review.reviewer_set.update(
            created=timezone.now(), modified=timezone.now()
        )
        review.follower_set.update(
            created=timezone.now(), modified=timezone.now()
        )
        for reviewer in review.reviewer_set.active():
            reviewer.create_reviewer_event(review.last_action_by)

        for follower in review.follower_set.active():
            follower.create_follower_event(review.last_action_by)


    def _reopen(self, review, prev_state):
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_OPENED,
            review,
            review.last_action_by
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewer_set.active()
        for user in users:
            is_reviewer = user in reviewers
            helpers.send_system_message(
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

        reviewers.update(status=constants.REVIEWING)
        review.reviewer_state = constants.REVIEWING
        review.save(update_fields=['reviewer_state'])
        models.Reminder.update_reminder_activity_for_review(review, True)

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        if prev_state.name == constants.DRAFT:
            self._open_draft(review)
            webhook_type = constants.CREATED
        elif prev_state.name in (constants.CLOSED, constants.ABORTED, constants.PAUSED):
            self._reopen(review, prev_state.name)
            webhook_type = constants.REOPENED

        self._common_state_change(review, webhook_type)


class Paused(State):

    name = constants.PAUSED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_PAUSED,
            review,
            review.last_action_by,
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            helpers.send_system_message(
                '"{}" has been Paused'.format(review.title),
                'demotime/messages/paused.html',
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


class Closed(State):

    name = constants.CLOSED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_CLOSED,
            review,
            review.last_action_by,
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            helpers.send_system_message(
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


class Aborted(State):

    name = constants.ABORTED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_ABORTED,
            review,
            review.last_action_by,
        )
        users = User.objects.filter(
            Q(reviewer__review=review, reviewer__is_active=True) |
            Q(follower__review=review, follower__is_active=True),
        ).distinct()
        reviewers = review.reviewers.all()
        for user in users:
            is_reviewer = user in reviewers
            helpers.send_system_message(
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


class Cancelled(State):

    name = constants.CANCELLED


class Reviewing(ReviewerState):

    name = constants.REVIEWING

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        helpers.send_system_message(
            '"{}" is back Under Review'.format(review.title),
            'demotime/messages/reviewing.html',
            {'review': review, 'previous_state': prev_state.name.title()},
            review.last_action_by,
            revision=review.revision,
        )
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_REVIEWING,
            review,
            review.last_action_by
        )
        self._common_state_change(review, constants.REVIEWING)


class Approved(ReviewerState):

    name = constants.APPROVED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        helpers.send_system_message(
            '"{}" has been Approved!'.format(review.title),
            'demotime/messages/approved.html',
            {'review': review},
            review.last_action_by,
            revision=review.revision,
        )
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_APPROVED,
            review,
            review.last_action_by
        )
        self._common_state_change(review, constants.APPROVED)


class Rejected(ReviewerState):

    name = constants.REJECTED

    def on_enter(self, review, prev_state):
        super().on_enter(review, prev_state)
        helpers.send_system_message(
            '"{}" has been Rejected'.format(review.title),
            'demotime/messages/rejected.html',
            {'review': review},
            review.last_action_by,
            revision=review.revision,
        )
        models.Event.create_event(
            review.project,
            models.EventType.DEMO_REJECTED,
            review,
            review.last_action_by
        )
        self._common_state_change(review, constants.REJECTED)


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
        constants.PAUSED: Paused,
    }


class ReviewerMachine(StateMachine):

    STATE_MAP = {
        constants.REVIEWING: Reviewing,
        constants.APPROVED: Approved,
        constants.REJECTED: Rejected,
    }
    STATE_FIELD = 'reviewer_state'
