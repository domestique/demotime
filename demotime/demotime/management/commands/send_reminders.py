from django.utils import timezone
from django.core.management.base import BaseCommand

from demotime import models


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting send_reminders')
        now = timezone.now()
        reminders = models.Reminder.objects.filter(remind_at__lte=now, active=True)
        count = 0
        for reminder in reminders:
            reminder.send_reminder()
            count +=1

        self.stdout.write('Sent {} reminders'.format(count))
