from datetime import timedelta

from django.core import mail
from django.utils import timezone

from demotime import models
from demotime.management.commands import send_reminders
from demotime.tests import BaseTestCase


class TestSendReminders(BaseTestCase):
    ''' Tests for demotime.management.commands.send_reminders.Command '''

    def setUp(self):
        super(TestSendReminders, self).setUp()
        self.command = send_reminders.Command()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Purging all of our reminders for testing ease
        models.Reminder.objects.all().delete()

    def test_send_reminders(self):
        mail.outbox = []
        models.Reminder.create_reminders_for_review(self.review)
        yesterday = timezone.now() - timedelta(days=1)
        models.Reminder.objects.update(remind_at=yesterday)
        last_reminder = models.Reminder.objects.filter(
            reminder_type=models.Reminder.REVIEWER
        ).last()
        last_reminder.remind_at = timezone.now() + timedelta(days=10)
        last_reminder.save(update_fields=['remind_at'])
        self.command.handle()

        self.assertEqual(models.Reminder.objects.count(), 4)
        self.assertEqual(len(mail.outbox), 3)
