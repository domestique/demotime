from django.utils import timezone
from django.core.management.base import BaseCommand

from demotime import models


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        now = timezone.now()
        reminders = models.Reminder.objects.filter(remind_at__lte=now, active=True)
        for reminder in reminders:
            print reminder
            reminder.send_reminder()
