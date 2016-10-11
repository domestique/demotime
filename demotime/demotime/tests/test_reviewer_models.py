from django.core import mail
from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestReviewerModels(BaseTestCase):

    def test_create_reviewer(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.all().delete()
        user = User.objects.get(username='test_user_0')
        reviewer = models.Reviewer.create_reviewer(obj, user, self.user, True)
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(reviewer.review.pk, obj.pk)
        self.assertEqual(reviewer.reviewer.pk, user.pk)
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(
            event.event_type.code, models.EventType.REVIEWER_ADDED
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, reviewer)

    def test_drop_reviewer(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        models.MessageBundle.objects.all().delete()
        reviewer = obj.reviewer_set.last()
        reviewer.drop_reviewer(obj.creator)
        self.assertEqual(models.MessageBundle.objects.count(), 1)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            1
        )
        event = models.Event.objects.get(
            event_type__code=models.EventType.REVIEWER_REMOVED
        )
        self.assertEqual(event.user, reviewer.reviewer)
        self.assertEqual(event.related_object, obj)

    def test_drop_reviewer_draft(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        models.MessageBundle.objects.all().delete()
        reviewer = obj.reviewer_set.last()
        reviewer.drop_reviewer(obj.creator, draft=True)
        self.assertEqual(models.MessageBundle.objects.count(), 0)
        self.assertEqual(
            models.Event.objects.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).count(),
            0
        )

    def test_reviewer_set_status(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        reviewer = obj.reviewer_set.all()[0]
        reminder = models.Reminder.objects.get(review=obj, user=reviewer.reviewer)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)
        reviewer.set_status(models.reviews.APPROVED)
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
            models.reviews.APPROVED
        )
        msg_bundle = models.MessageBundle.objects.get(
            review=obj,
            owner=obj.creator
        )
        self.assertEqual(
            msg_bundle.message_set.first().title,
            '{} has approved your review: {}'.format(
                reviewer.reviewer_display_name, obj.title
            )
        )
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)

        reviewer.set_status(models.reviews.REJECTED)
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
            models.reviews.REJECTED
        )
        self.assertEqual(
            msg_bundle.message_set.first().title,
            '{} has rejected your review: {}'.format(
                reviewer.reviewer_display_name, obj.title
            )
        )
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)

        reviewer.set_status(models.reviews.REVIEWING)
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
            models.reviews.REVIEWING
        )
        self.assertEqual(
            msg_bundle.message_set.first().title,
            '{} resumed reviewing your review: {}'.format(
                reviewer.reviewer_display_name, obj.title
            )
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
        self.assertTrue(
            reviewer_obj.reviewer.messagebundle_set.filter(
                review=review,
                message__title='You have been added as a reviewer on: {}'.format(review.title),
                read=False,
            ).exists()
        )
        self.assertFalse(
            review.creator.messagebundle_set.filter(
                review=review,
                message__title='{} has been added as a reviewer on: {}'.format(
                    reviewer_obj.reviewer_display_name,
                    review.title
                ),
                read=False,
            ).exists()
        )

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
        self.assertFalse(
            reviewer_obj.reviewer.messagebundle_set.filter(
                review=review,
                message__title='You have been added as a reviewer on: {}'.format(review.title),
                read=False,
            ).exists()
        )
        self.assertTrue(
            review.creator.messagebundle_set.filter(
                review=review,
                message__title='{} has been added as a reviewer on: {}'.format(
                    reviewer_obj.reviewer_display_name,
                    review.title
                ),
                read=False,
            ).exists()
        )

    def test_reviewer_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        reviewer = review.reviewer_set.all()[0]
        reviewer_json = reviewer.to_json()
        self.assertEqual(reviewer_json['name'], reviewer.reviewer.userprofile.name)
        self.assertEqual(reviewer_json['user_pk'], reviewer.reviewer.pk)
        self.assertEqual(reviewer_json['reviewer_pk'], reviewer.pk)
        self.assertEqual(reviewer_json['review_pk'], reviewer.review.pk)
