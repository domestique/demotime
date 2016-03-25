import bdateutil

from django.db import models
from django.conf import settings
from django.utils import timezone

from .base import BaseModel
from .messages import Message


def get_reminder_days():
    return timezone.now() + bdateutil.relativedelta(
        bdays=settings.DEFAULT_REMINDER_DAYS
    )


class Reminder(BaseModel):

    CREATOR = 'creator'
    REVIEWER = 'reviewer'

    REMINDER_TYPES = (
        (CREATOR, CREATOR.capitalize()),
        (REVIEWER, REVIEWER.capitalize()),
    )

    review = models.ForeignKey('Review')
    user = models.ForeignKey('auth.User')
    reminder_type = models.CharField(
        max_length=256,
        choices=REMINDER_TYPES,
        db_index=True,
    )
    remind_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return '{} Reminder for {} on {}'.format(
            self.reminder_type,
            self.user.username,
            self.review.title
        )

    @classmethod
    def create_reminder(cls, review, user, reminder_type, remind_at=None):
        if not remind_at:
            remind_at = get_reminder_days()
        return cls.objects.create(
            review=review,
            user=user,
            reminder_type=reminder_type,
            remind_at=remind_at,
        )

    @classmethod
    def create_reminders_for_review(cls, review):
        cls.create_reminder(
            review=review,
            user=review.creator,
            reminder_type=cls.CREATOR
        )
        for reviewer in review.reviewer_set.all():
            cls.create_reminder(
                review=review,
                user=reviewer.reviewer,
                reminder_type=cls.REVIEWER
            )

    @classmethod
    def update_reminders_for_review(cls, review):
        remind_at = get_reminder_days()

        # Creator Reminder
        try:
            creator_reminder = cls.objects.get(review=review, user=review.creator)
        except cls.DoesNotExist:
            creator_reminder = cls(review=review, user=review.creator, reminder_type=cls.CREATOR)
        creator_reminder.remind_at = remind_at
        creator_reminder.active = True
        creator_reminder.save()

        # Reviewer Reminders
        cls.objects.exclude(user__in=review.reviewers.all()).exclude(
            user=review.creator).delete()
        cls.objects.filter(user__in=review.reviewers.all()).update(
            remind_at=remind_at
        )

        cls.objects.filter(review=review).update(active=True)

    @classmethod
    def update_reminder_activity_for_review(cls, review, active=False):
        if active:
            cls.objects.filter(review=review).update(
                active=active,
                remind_at=get_reminder_days(),
            )
        else:
            cls.objects.filter(review=review).update(active=active)

    @classmethod
    def set_activity(cls, review, user, active=False):
        if active:
            cls.objects.filter(review=review, user=user).update(
                active=active,
                remind_at=get_reminder_days(),
            )
        else:
            cls.objects.filter(review=review, user=user).update(active=active)

    def send_reminder(self):
        context = {
            'reminder': self,
            'url': self.review.get_absolute_url(),
        }
        title = 'Reminder: {}'.format(self.review.title)
        Message.send_system_message(
            title,
            'demotime/messages/reminder.html',
            context,
            self.user,
        )
        self.remind_at = get_reminder_days()
        self.save(update_fields=['remind_at'])

    class Meta:
        unique_together = (
            ('review', 'user')
        )
