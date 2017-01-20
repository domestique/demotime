from datetime import datetime

from django.core import mail
from django.contrib.auth.models import User

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReviewerModels(BaseTestCase):

    def test_create_reviewer(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.all().delete()
        user = User.objects.get(username='test_user_0')
        reviewer = models.Reviewer.create_reviewer(obj, user, self.user, True)
        self.assertEqual(reviewer.status, constants.REVIEWING)
        self.assertEqual(reviewer.review.pk, obj.pk)
        self.assertEqual(reviewer.reviewer.pk, user.pk)
        self.assertTrue(reviewer.is_active)
        self.assertIsNone(reviewer.last_viewed)
        reminders = models.Reminder.objects.filter(
            review=obj, user=user
        )
        self.assertEqual(reminders.count(), 1)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, reviewer)

    def test_set_viewed(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        reviewer = obj.reviewer_set.all()[0]
        self.assertIsNone(reviewer.last_viewed)
        reviewer.viewed_review()
        self.assertIsInstance(reviewer.last_viewed, datetime)

    def test_deleting_and_creating_reviewer(self):
        ''' Reminder should be created, reviewer flips back to active '''
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.all().delete()
        user = User.objects.get(username='test_user_0')
        reminders = models.Reminder.objects.filter(
            review=obj, user=user
        )
        # Create
        reviewer = models.Reviewer.create_reviewer(obj, user, self.user, True)
        reminders = models.Reminder.objects.filter(
            review=obj, user=user
        )
        self.assertTrue(reviewer.is_active)
        self.assertIsNone(reviewer.last_viewed)
        self.assertEqual(reminders.count(), 1)
        # Delete
        reviewer.drop_reviewer(user, user)
        reviewer.refresh_from_db()
        reminders = models.Reminder.objects.filter(
            review=obj, user=user
        )
        self.assertFalse(reviewer.is_active)
        self.assertEqual(reminders.count(), 0)
        # Recreate
        reviewer = models.Reviewer.create_reviewer(obj, user, self.user, True)
        reminders = models.Reminder.objects.filter(
            review=obj, user=user
        )
        self.assertTrue(reviewer.is_active)
        self.assertEqual(reminders.count(), 1)

    def test_create_reviewer_resets_state(self):
        test_user = User.objects.get(username='test_user_0')
        self.default_review_kwargs['reviewers'] = self.test_users.exclude(
            username=test_user.username
        )
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        for reviewer in obj.reviewer_set.all():
            reviewer.set_status(constants.APPROVED)

        obj.refresh_from_db()
        self.assertEqual(obj.reviewer_state, constants.APPROVED)
        models.Reviewer.create_reviewer(obj, test_user, self.user, True)
        obj.refresh_from_db()
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)

    def test_drop_reviewer(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        mail.outbox = []
        reviewer = obj.reviewer_set.last()
        reviewer.drop_reviewer(obj.creator_set.active().get().user)
        reviewer.refresh_from_db()
        reminders = models.Reminder.objects.filter(
            review=obj, user=reviewer.reviewer
        )
        self.assertFalse(reviewer.is_active)
        self.assertFalse(reminders.exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            1
        )
        event = models.Event.objects.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertEqual(event.related_object, reviewer)

    def test_drop_reviewer_draft(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        mail.outbox = []
        reviewer = obj.reviewer_set.last()
        reviewer.drop_reviewer(obj.creator_set.active().get().user, draft=True)
        reviewer.refresh_from_db()
        self.assertFalse(reviewer.is_active)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            0
        )

    def test_drop_reviewer_updates_state_approved(self):
        test_user_1 = User.objects.get(username='test_user_1')
        obj = models.Review.create_review(**self.default_review_kwargs)
        models.Reviewer.objects.exclude(reviewer=test_user_1).update(
            status=constants.APPROVED
        )
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        reviewer = models.Reviewer.objects.get(reviewer=test_user_1)
        reviewer.drop_reviewer(obj.creator_set.active().get().user)
        obj.refresh_from_db()
        self.assertEqual(len(mail.outbox), 6)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            1
        )
        event = models.Event.objects.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertEqual(event.related_object, reviewer)
        self.assertEqual(obj.reviewer_state, constants.APPROVED)

    def test_drop_reviewer_updates_state_rejected(self):
        test_user_1 = User.objects.get(username='test_user_1')
        obj = models.Review.create_review(**self.default_review_kwargs)
        models.Reviewer.objects.exclude(reviewer=test_user_1).update(
            status=constants.REJECTED
        )
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        reviewer = models.Reviewer.objects.get(reviewer=test_user_1)
        reviewer.drop_reviewer(obj.creator_set.active().get().user)
        obj.refresh_from_db()
        self.assertEqual(len(mail.outbox), 6)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            1
        )
        event = models.Event.objects.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, obj.creator_set.active().get().user)
        self.assertEqual(event.related_object, reviewer)
        self.assertEqual(obj.reviewer_state, constants.REJECTED)

    def test_reviewer_set_status(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        reviewer = obj.reviewer_set.all()[0]
        reminder = models.Reminder.objects.get(review=obj, user=reviewer.reviewer)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)
        reviewer.set_status(constants.APPROVED)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_APPROVED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_APPROVED
        )
        self.assertEqual(event.user, reviewer.reviewer)
        self.assertEqual(event.related_object, reviewer)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            constants.APPROVED
        )
        status_msg = []
        creator = obj.creator_set.active().get().user
        for msg in mail.outbox:
            if msg.to == [creator.email] and 'approved' in msg.body:
                status_msg.append(msg)

        self.assertEqual(len(status_msg), 1)
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)

        reviewer.set_status(constants.REJECTED)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_REJECTED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_REJECTED
        )
        self.assertEqual(event.user, reviewer.reviewer)
        self.assertEqual(event.related_object, reviewer)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            constants.REJECTED
        )
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)

        reviewer.set_status(constants.REVIEWING)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_RESET
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_RESET
        )
        self.assertEqual(event.user, reviewer.reviewer)
        self.assertEqual(event.related_object, reviewer)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            constants.REVIEWING
        )
        self.assertTrue(models.Reminder.objects.get(pk=reminder.pk).active)

    def test_create_reviewer_notify_reviewer(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.all().delete()
        self.assertEqual(review.reviewer_set.count(), 0)
        mail.outbox = []
        new_reviewer = User.objects.get(username='test_user_0')
        reviewer_obj = models.Reviewer.create_reviewer(
            review, new_reviewer, self.user
        )
        event = reviewer_obj.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, reviewer_obj)

        # We email on non-revision
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(review.reviewer_set.count(), 1)
        self.assertEqual(reviewer_obj.review, review)
        self.assertEqual(reviewer_obj.reviewer, new_reviewer)

    def test_create_reviewer_notify_creator(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.all().delete()
        self.assertEqual(review.reviewer_set.count(), 0)
        mail.outbox = []
        new_reviewer = User.objects.get(username='test_user_0')
        reviewer_obj = models.Reviewer.create_reviewer(
            review, new_reviewer, new_reviewer
        )
        event = reviewer_obj.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, reviewer_obj.reviewer)
        self.assertEqual(event.related_object, reviewer_obj)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(review.reviewer_set.count(), 1)
        self.assertEqual(reviewer_obj.review, review)
        self.assertEqual(reviewer_obj.reviewer, new_reviewer)

    def test_reviewer_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        reviewer = review.reviewer_set.all()[0]
        reviewer.last_viewed = datetime.now()
        reviewer_json = reviewer.to_json()
        self.assertEqual(reviewer_json['name'], reviewer.reviewer.userprofile.name)
        self.assertEqual(reviewer_json['user_pk'], reviewer.reviewer.pk)
        self.assertEqual(reviewer_json['reviewer_pk'], reviewer.pk)
        self.assertEqual(reviewer_json['review_pk'], reviewer.review.pk)
        self.assertEqual(reviewer_json['last_viewed'], reviewer.last_viewed.isoformat())
        self.assertEqual(
            reviewer_json['user_profile_url'],
            reviewer.reviewer.userprofile.get_absolute_url()
        )
        expected_keys = [
            'name', 'user_pk', 'user_profile_url', 'reviewer_pk',
            'reviewer_status', 'review_pk', 'last_viewed', 'is_active',
            'created', 'modified'
        ]
        self.assertEqual(
            sorted(reviewer_json.keys()),
            sorted(expected_keys)
        )
