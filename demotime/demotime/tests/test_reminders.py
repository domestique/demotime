import pytz
from datetime import datetime

from freezegun import freeze_time
from django.contrib.auth.models import User
from django.utils import timezone

from demotime import models
from demotime.tests import BaseTestCase


# It's a month that starts on a Monday, convenient
@freeze_time('2014-12-01')
class TestReminderModel(BaseTestCase):

    def setUp(self):
        super(TestReminderModel, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Purging all of our reminders for testing ease
        models.Reminder.objects.all().delete()

    def test_create_reminder(self):
        reminder = models.Reminder.create_reminder(
            self.review,
            self.review.creator,
            models.Reminder.CREATOR
        )
        self.assertEqual(reminder.user, self.review.creator)
        self.assertEqual(reminder.review, self.review)
        self.assertEqual(reminder.reminder_type, models.Reminder.CREATOR)
        self.assertEqual(
            reminder.remind_at,
            timezone.make_aware(datetime(2014, 12, 3), pytz.utc)
        )
        self.assertEqual(reminder.active, True)

    def test_create_reminder_with_dt(self):
        remind_dt = timezone.make_aware(datetime(2014, 12, 25), pytz.utc)
        reminder = models.Reminder.create_reminder(
            self.review,
            self.review.creator,
            models.Reminder.CREATOR,
            remind_at=remind_dt,
        )
        self.assertEqual(reminder.user, self.review.creator)
        self.assertEqual(reminder.review, self.review)
        self.assertEqual(reminder.reminder_type, models.Reminder.CREATOR)
        self.assertEqual(
            reminder.remind_at,
            remind_dt,
        )
        self.assertEqual(reminder.active, True)

    def test_create_reminders_for_review(self):
        models.Reminder.create_reminders_for_review(self.review)
        reminders = models.Reminder.objects.filter(review=self.review, active=True)
        self.assertEqual(reminders.count(), 4)
        self.assertEqual(
            reminders.filter(reminder_type=models.Reminder.REVIEWER).count(),
            3
        )
        self.assertEqual(
            reminders.filter(reminder_type=models.Reminder.CREATOR).count(),
            1
        )

    def test_update_reminders_for_review(self):
        # Create reminders first
        models.Reminder.create_reminders_for_review(self.review)
        # Disable all of them, as if the reviewers approved
        models.Reminder.objects.filter(review=self.review).update(active=False)
        self.review.reviewer_set.filter(
            reviewer=User.objects.get(username='test_user_0')
        ).delete()
        # Update the reminders
        models.Reminder.update_reminders_for_review(self.review)

        # Do the test things
        reminders = models.Reminder.objects.filter(review=self.review, active=True)
        self.assertEqual(reminders.count(), 3)
        self.assertEqual(
            reminders.filter(reminder_type=models.Reminder.REVIEWER).count(),
            2
        )
        self.assertEqual(
            reminders.filter(reminder_type=models.Reminder.CREATOR).count(),
            1
        )

    def test_update_reminder_activity_for_review(self):
        models.Reminder.create_reminders_for_review(self.review)
        models.Reminder.objects.filter(review=self.review).update(active=False)

        models.Reminder.update_reminder_activity_for_review(self.review, True)
        self.assertEqual(
            models.Reminder.objects.filter(review=self.review, active=True).count(),
            4
        )
        self.assertEqual(
            models.Reminder.objects.filter(
                review=self.review
            ).values_list('remind_at', flat=True).distinct().get(),
            timezone.make_aware(datetime(2014, 12, 3), pytz.utc)
        )

        models.Reminder.update_reminder_activity_for_review(self.review, False)
        self.assertEqual(
            models.Reminder.objects.filter(review=self.review, active=False).count(),
            4
        )

    def test_set_activity(self):
        models.Reminder.create_reminders_for_review(self.review)
        models.Reminder.objects.filter(review=self.review).update(active=False)

        models.Reminder.set_activity(self.review, self.review.creator, True)
        reminder = models.Reminder.objects.get(
            review=self.review, user=self.review.creator
        )
        self.assertTrue(reminder.active)
        self.assertEqual(
            reminder.remind_at,
            timezone.make_aware(datetime(2014, 12, 3), pytz.utc)
        )

        models.Reminder.set_activity(self.review, self.review.creator, False)
        reminder = models.Reminder.objects.get(
            review=self.review, user=self.review.creator
        )
        self.assertFalse(reminder.active)
