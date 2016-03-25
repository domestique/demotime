from django.core import mail
from django.contrib.auth.models import User

from demotime import models
from demotime.tests import BaseTestCase


class TestReviewModels(BaseTestCase):

    def test_create_review(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.state, models.reviews.OPEN)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 4)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 3)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_update_review(self):
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
        })
        new_obj = models.Review.update_review(**review_kwargs)
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)
        # FIXME: Issue 55
        #self.assertEqual(obj.reviewers.count(), 2)
        #self.assertEqual(obj.reviewer_set.count(), 2)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 4)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 3)
        #self.assertEqual(len(mail.outbox), 2)
        #self.assertEqual(
        #    models.Reminder.objects.filter(review=obj, active=True).count(),
        #    3
        #)

    def test_create_reviewer(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.all().delete()
        user = User.objects.get(username='test_user_0')
        reviewer = models.Reviewer.create_reviewer(obj, user)
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(reviewer.review.pk, obj.pk)
        self.assertEqual(reviewer.reviewer.pk, user.pk)

    def test_reviewer_set_status(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        reviewer = obj.reviewer_set.all()[0]
        reminder = models.Reminder.objects.get(review=obj, user=reviewer.reviewer)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)
        reviewer.set_status(models.reviews.APPROVED)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.APPROVED
        )
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)
        reviewer.set_status(models.reviews.REJECTED)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.REJECTED
        )
        self.assertFalse(models.Reminder.objects.get(pk=reminder.pk).active)
        models.Reminder.objects.filter(pk=reminder.pk).update(active=True)
        reviewer.set_status(models.reviews.REVIEWING)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.REVIEWING
        )
        self.assertTrue(models.Reminder.objects.get(pk=reminder.pk).active)

    def test_update_reviewer_state_approved(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        obj.reviewer_set.update(status=models.reviews.APPROVED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.APPROVED)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" has been Approved!'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.APPROVED)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_update_reviewer_state_rejected(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        obj.reviewer_set.update(status=models.reviews.REJECTED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.REJECTED)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" has been Rejected'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.REJECTED)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_update_reviewer_state_reviewing(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        obj.reviewer_set.update(status=models.reviews.REJECTED)
        obj.reviewer_state = models.reviews.REJECTED
        obj.save(update_fields=['reviewer_state'])
        undecided_person = obj.reviewer_set.all()[0]
        undecided_person.status = models.reviews.REVIEWING
        undecided_person.save()
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" is back Under Review'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.REVIEWING)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_update_reviewer_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        changed, new_state = obj.update_reviewer_state()
        self.assertFalse(changed)
        self.assertEqual(new_state, '')

    def test_review_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertFalse(obj.update_state(models.reviews.OPEN))

    def test_review_state_change_closed(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(models.reviews.CLOSED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.CLOSED)
        msgs = models.Message.objects.filter(
            review=obj,
            title='"{}" has been {}'.format(
                obj.title, models.reviews.CLOSED.capitalize()
            )
        )
        self.assertEqual(msgs.count(), 3)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            3
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            4
        )

    def test_review_state_change_aborted(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(models.reviews.ABORTED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.ABORTED)
        msgs = models.Message.objects.filter(review=obj)
        msgs = models.Message.objects.filter(
            review=obj,
            title='"{}" has been {}'.format(
                obj.title, models.reviews.ABORTED.capitalize()
            )
        )
        self.assertEqual(msgs.count(), 3)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            3
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            4
        )

    def test_review_state_change_closed_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        obj.state = models.reviews.CLOSED
        obj.save(update_fields=['state'])
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(models.reviews.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.OPEN)
        msgs = models.Message.objects.filter(review=obj)
        msgs = models.Message.objects.filter(
            review=obj,
            title='"{}" has been Reopened'.format(obj.title)
        )
        self.assertEqual(msgs.count(), 3)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            3
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_review_state_change_aborted_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox = []

        obj.state = models.reviews.ABORTED
        obj.save(update_fields=['state'])
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(models.reviews.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.OPEN)
        msgs = models.Message.objects.filter(review=obj)
        msgs = models.Message.objects.filter(
            review=obj,
            title='"{}" has been Reopened'.format(obj.title)
        )
        self.assertEqual(msgs.count(), 3)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            3
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
