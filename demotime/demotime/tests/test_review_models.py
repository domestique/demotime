from mock import patch

from django.core import mail
from django.contrib.auth.models import User

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReviewModels(BaseTestCase):

    def setUp(self):
        super(TestReviewModels, self).setUp()
        self.hook_patch = patch('demotime.models.reviews.Review.trigger_webhooks')
        self.hook_patch_run = self.hook_patch.start()
        self.addCleanup(self.hook_patch.stop)

    def test_create_review(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.hook_patch_run.assert_called_once_with(
            constants.CREATED
        )
        event = obj.event_set.get(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_CREATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)

    def test_create_draft_review(self):
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.DRAFT)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(
            models.Reminder.objects.filter(review=obj, active=True).exists()
        )
        self.hook_patch_run.assert_not_called()
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )

    def test_update_draft_review(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 0)
        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        # Should still be the same, singular revision
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(obj.revision.attachments.count(), 4)
        self.assertEqual(obj.description, 'New Description')
        self.assertEqual(obj.case_link, 'http://badexample.org')
        self.assertFalse(
            models.Reminder.objects.filter(review=obj, active=True).exists()
        )
        self.hook_patch_run.assert_not_called()
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).exists()
        )
        self.assertFalse(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )

    def test_draft_review_opened(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        obj = models.Review.create_review(**self.default_review_kwargs)
        created_time = obj.created
        self.assertEqual(len(mail.outbox), 0)
        self.default_review_kwargs['state'] = constants.OPEN
        self.default_review_kwargs['review'] = obj.pk
        obj = models.Review.update_review(**self.default_review_kwargs)
        self.assertNotEqual(created_time, obj.created)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 5)
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).exists()
        )
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.REVIEWER_ADDED
            ).exists()
        )
        self.assertTrue(
            obj.event_set.filter(
                event_type__code=models.EventType.FOLLOWER_ADDED
            ).exists()
        )
        self.hook_patch_run.assert_called_once_with(
            constants.CREATED
        )

    def test_create_review_duped_reviewer_follower(self):
        ''' Test creating a review with a user in both the Reviwers and the
        Followers list
        '''
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        user_pks = list(self.test_users.values_list('pk', flat=True))
        user_pks += list(self.followers.values_list('pk', flat=True))
        review_kwargs['followers'] = User.objects.filter(pk__in=user_pks)
        obj = models.Review.create_review(**review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        attachment = obj.revision.attachments.all()[0]
        attachment.attachment.name = 'test/test_file'
        self.assertEqual(attachment.pretty_name, 'test_file')
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_update_review(self):
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        # We had problems before where updating one review's reviewers updated
        # the reviewer's for alllllll reviews. Let's not let that happen again
        # (issue #55)
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Some Other Review'
        obj = models.Review.create_review(**self.default_review_kwargs)
        first_rev = obj.revision
        second_review = models.Review.create_review(**second_review_kwargs)
        self.assertEqual(obj.reviewers.count(), 3)
        approving_reviewer = obj.reviewer_set.all()[0]
        approving_reviewer.status = models.reviews.APPROVED
        approving_reviewer.save()
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(second_review.reviewers.count(), 3)
        self.assertEqual(len(mail.outbox), 10)
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
        event = new_obj.event_set.get(
            event_type__code=models.EventType.DEMO_UPDATED
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        second_rev = new_obj.revision
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)
        self.assertEqual(new_obj.revision.number, 2)
        self.assertTrue(new_obj.revision.is_max_revision)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.follower_set.count(), 2)
        for reviewer in obj.reviewer_set.all():
            self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        self.assertEqual(second_review.reviewers.count(), 3)
        self.assertEqual(second_review.reviewer_set.count(), 3)
        self.assertEqual(second_review.follower_set.count(), 2)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            3
        )
        # Since we didn't supply attachments in the update, they should be
        # copied over
        self.assertEqual(
            first_rev.attachments.count(),
            second_rev.attachments.count()
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        # Second demo
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[2][0][0],
            constants.UPDATED,
        )

    def test_update_closed_review(self):
        ''' Updating a closed review should reopen it '''
        obj = models.Review.create_review(**self.default_review_kwargs)
        for reviewer in obj.reviewer_set.all():
            reviewer.set_status(constants.APPROVED)
        obj.update_state(constants.CLOSED)
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(obj.state, constants.CLOSED)
        self.assertEqual(obj.reviewer_state, constants.APPROVED)
        models.UserReviewStatus.objects.filter(review=obj).update(read=True)
        self.default_review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
            'reviewers': self.test_users.exclude(username='test_user_0'),
        })
        obj = models.Review.update_review(**self.default_review_kwargs)
        # Should still be the same, singular revision
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.description, 'New Description')
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(obj.revision.number, 2)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)

    def test_update_review_duped_reviewer_follower(self):
        self.assertEqual(len(mail.outbox), 0)
        review_kwargs = self.default_review_kwargs.copy()
        user_pks = list(self.test_users.values_list('pk', flat=True))
        user_pks += list(self.followers.values_list('pk', flat=True))
        review_kwargs['followers'] = User.objects.filter(pk__in=user_pks)
        obj = models.Review.create_review(**review_kwargs)
        first_rev = obj.revision
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.follower_set.count(), 2)
        approving_reviewer = obj.reviewer_set.all()[0]
        approving_reviewer.status = models.reviews.APPROVED
        approving_reviewer.save()
        self.assertEqual(obj.revision.number, 1)
        self.assertEqual(len(mail.outbox), 5)
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
        second_rev = new_obj.revision
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)
        self.assertEqual(new_obj.revision.number, 2)
        self.assertTrue(new_obj.revision.is_max_revision)
        self.assertEqual(obj.reviewer_set.active().count(), 2)
        self.assertEqual(obj.reviewer_set.count(), 3)
        self.assertEqual(obj.follower_set.count(), 2)
        for reviewer in obj.reviewer_set.all():
            self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        statuses = models.UserReviewStatus.objects.filter(review=obj)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            3
        )
        # Since we didn't supply attachments in the update, they should be
        # copied over
        self.assertEqual(
            first_rev.attachments.count(),
            second_rev.attachments.count()
        )

    def test_update_reviewer_state_approved(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.reviewer_set.update(status=models.reviews.APPROVED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.APPROVED)
        msg = models.Message.objects.get(
            review=obj.reviewrevision_set.latest(),
            receipient=obj.creator
        )
        self.assertEqual(msg.title, '"{}" has been Approved!'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.APPROVED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_APPROVED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_APPROVED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        self.assertTrue(
            models.UserReviewStatus.objects.filter(
                review=obj,
                user=self.user,
                read=False
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.APPROVED
        )

    def test_update_reviewer_state_rejected(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.reviewer_set.update(status=models.reviews.REJECTED)
        models.UserReviewStatus.objects.update(read=True)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.REJECTED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_REJECTED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_REJECTED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        msg = models.Message.objects.get(
            review=obj.reviewrevision_set.latest(),
            receipient=obj.creator
        )
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
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.REJECTED
        )

    def test_update_reviewer_state_reviewing(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
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
        msg = models.Message.objects.get(
            review=obj.reviewrevision_set.latest(), receipient=obj.creator
        )
        self.assertEqual(msg.title, '"{}" is back Under Review'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.REVIEWING)
        event = obj.event_set.get(
            event_type__code=models.EventType.DEMO_REVIEWING
        )
        self.assertEqual(event.event_type.code, event.event_type.DEMO_REVIEWING)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
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
        self.assertFalse(obj.update_state(constants.OPEN))

    def test_review_state_change_closed(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(models.reviews.CLOSED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.CLOSED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_CLOSED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_CLOSED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        msgs = models.Message.objects.filter(
            review=obj.reviewrevision_set.latest(),
            title='"{}" has been {}'.format(
                obj.title, models.reviews.CLOSED.capitalize()
            )
        )
        self.assertEqual(msgs.count(), 5)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.CLOSED,
        )

    def test_review_state_change_aborted(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=True)
        self.assertTrue(obj.update_state(models.reviews.ABORTED))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, models.reviews.ABORTED)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_ABORTED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_ABORTED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        msgs = models.Message.objects.filter(review=obj.reviewrevision_set.latest())
        msgs = models.Message.objects.filter(
            review=obj.reviewrevision_set.latest(),
            title='"{}" has been {}'.format(
                obj.title, models.reviews.ABORTED.capitalize()
            )
        )
        self.assertEqual(msgs.count(), 5)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=False).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.ABORTED
        )

    def test_review_state_change_closed_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.state = models.reviews.CLOSED
        obj.save(update_fields=['state'])
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(constants.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.OPEN)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_OPENED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_OPENED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        msgs = models.Message.objects.filter(review=obj.reviewrevision_set.latest())
        msgs = models.Message.objects.filter(
            review=obj.reviewrevision_set.latest(),
            title='"{}" has been Reopened'.format(obj.title)
        )
        self.assertEqual(msgs.count(), 5)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.REOPENED,
        )

    def test_review_state_change_aborted_to_open(self):
        self.assertEqual(len(mail.outbox), 0)
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(len(mail.outbox), 5)
        mail.outbox = []

        obj.state = models.reviews.ABORTED
        obj.save(update_fields=['state'])
        models.UserReviewStatus.objects.update(read=True)
        models.Reminder.objects.filter(review=obj).update(active=False)
        self.assertTrue(obj.update_state(constants.OPEN))
        # refresh it
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.state, constants.OPEN)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_OPENED)
        self.assertEqual(event.event_type.code, event.event_type.DEMO_OPENED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(event.user, obj.creator)
        msgs = models.Message.objects.filter(review=obj.reviewrevision_set.latest())
        msgs = models.Message.objects.filter(
            review=obj.reviewrevision_set.latest(),
            title='"{}" has been Reopened'.format(obj.title)
        )
        self.assertEqual(msgs.count(), 5)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[0][0][0],
            constants.CREATED
        )
        self.assertEqual(
            self.hook_patch_run.call_args_list[1][0][0],
            constants.REOPENED,
        )

    def test_reviewer_status_count_properties_reviewing(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewing_count, 3)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 0)

    def test_reviewer_status_count_properties_approved(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.update(status=models.reviews.APPROVED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 3)
        self.assertEqual(review.rejected_count, 0)

    def test_reviewer_status_count_properties_rejected(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review.reviewer_set.update(status=models.reviews.REJECTED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 3)

    def test_reviewer_status_count_properties_deleted(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        reviewer = review.reviewer_set.all()[0]
        reviewer.drop_reviewer(review.creator)
        self.assertEqual(review.reviewing_count, 2)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 0)

        review.reviewer_set.update(status=models.reviews.REJECTED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 0)
        self.assertEqual(review.rejected_count, 2)

        review.reviewer_set.update(status=models.reviews.APPROVED)
        self.assertEqual(review.reviewing_count, 0)
        self.assertEqual(review.approved_count, 2)
        self.assertEqual(review.rejected_count, 0)

    def test_review_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        review_json = review.to_json()
        self.assertEqual(review_json['title'], review.title)
        self.assertEqual(review_json['creator'], review.creator.userprofile.name)
        reviewers = []
        for reviewer in review.reviewer_set.active():
            reviewers.append(reviewer.to_json())

        followers = []
        for follower in review.follower_set.active():
            followers.append(follower.to_json())

        self.assertEqual(review_json['reviewers'], reviewers)
        self.assertEqual(review_json['followers'], followers)
        self.assertEqual(review_json['description'], review.description)
        self.assertEqual(review_json['case_link'], review.case_link)
        self.assertEqual(review_json['state'], review.state)
        self.assertEqual(review_json['reviewer_state'], review.reviewer_state)
        self.assertEqual(review_json['is_public'], review.is_public)
        self.assertEqual(review_json['project'], {
            'id': review.project.pk,
            'slug': review.project.slug,
            'name': review.project.name,
        })
        self.assertEqual(review_json['url'], review.get_absolute_url())
        self.assertEqual(review_json['reviewing_count'], review.reviewing_count)
        self.assertEqual(review_json['approved_count'], review.approved_count)
        self.assertEqual(review_json['rejected_count'], review.rejected_count)

    def test_review_to_json_hides_inactive_reviews_followers(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        self.assertEqual(review.reviewer_set.count(), 3)
        self.assertEqual(review.follower_set.count(), 2)
        # Drop a reviewer and follower
        reviewer = review.reviewer_set.all()[0]
        follower = review.follower_set.all()[0]
        reviewer.drop_reviewer(review.creator)
        follower.drop_follower(review.creator)
        # Verify things are as they should be
        self.assertEqual(review.reviewer_set.count(), 3)
        self.assertEqual(review.follower_set.count(), 2)
        self.assertEqual(review.reviewer_set.active().count(), 2)
        self.assertEqual(review.follower_set.active().count(), 1)

        review_json = review.to_json()
        reviewers = []
        for reviewer in review.reviewer_set.active():
            reviewers.append(reviewer.to_json())

        followers = []
        for follower in review.follower_set.active():
            followers.append(follower.to_json())

        self.assertEqual(review_json['reviewers'], reviewers)
        self.assertEqual(review_json['followers'], followers)
        self.assertEqual(len(review_json['reviewers']), 2)
        self.assertEqual(len(review_json['followers']), 1)

    @patch('demotime.tasks.fire_webhook')
    def test_trigger_webhooks_fires(self, task_patch):
        review = models.Review.create_review(**self.default_review_kwargs)
        hook = models.WebHook.objects.create(
            project=review.project,
            trigger_event=constants.CREATED,
            target='http://www.example.com'
        )
        self.hook_patch.stop()

        review.trigger_webhooks(constants.CREATED)
        task_patch.delay.assert_called_once_with(
            review.pk,
            hook.pk,
            None
        )
        self.hook_patch.start()

    @patch('demotime.tasks.fire_webhook')
    def test_trigger_webhooks_skipped(self, task_patch):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.WebHook.objects.create(
            project=review.project,
            trigger_event=constants.CLOSED,
            target='http://www.example.com'
        )
        self.hook_patch.stop()

        review.trigger_webhooks(constants.CREATED)
        self.assertFalse(task_patch.called)
        self.hook_patch.start()
