from django.contrib.auth.models import User
from django.core.files.uploadedfile import BytesIO, File

from demotime import models
from demotime.tests import BaseTestCase


class TestDemoTimeModels(BaseTestCase):

    def test_create_review(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        assert obj.revision
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, 'Test Title')
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.case_link, 'http://example.org/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.state, models.reviews.OPEN)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)

    def test_update_review(self):
        review_kwargs = self.default_review_kwargs.copy()
        obj = models.Review.create_review(**self.default_review_kwargs)
        review_kwargs.update({
            'review': obj.pk,
            'title': 'New Title',
            'description': 'New Description',
            'case_link': 'http://badexample.org',
        })
        new_obj = models.Review.update_review(**review_kwargs)
        self.assertEqual(obj.pk, new_obj.pk)
        self.assertEqual(new_obj.title, 'New Title')
        self.assertEqual(new_obj.case_link, 'http://badexample.org')
        # Desc should be unchanged
        self.assertEqual(new_obj.description, 'Test Description')
        self.assertEqual(new_obj.revision.description, 'New Description')
        self.assertEqual(new_obj.reviewrevision_set.count(), 2)

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
        reviewer.set_status(models.reviews.APPROVED)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.APPROVED
        )
        reviewer.set_status(models.reviews.REJECTED)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.REJECTED
        )
        reviewer.set_status(models.reviews.REVIEWING)
        self.assertEqual(
            models.Reviewer.objects.get(pk=reviewer.pk).status,
            models.reviews.REVIEWING
        )

    def test_update_reviewer_state_approved(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.update(status=models.reviews.APPROVED)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.APPROVED)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" has been Approved!'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.APPROVED)

    def test_update_reviewer_state_rejected(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.update(status=models.reviews.REJECTED)
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.REJECTED)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" has been Rejected'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.REJECTED)

    def test_update_reviewer_state_reviewing(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.reviewer_set.update(status=models.reviews.REJECTED)
        obj.reviewer_state = models.reviews.REJECTED
        obj.save(update_fields=['reviewer_state'])
        undecided_person = obj.reviewer_set.all()[0]
        undecided_person.status = models.reviews.REVIEWING
        undecided_person.save()
        changed, new_state = obj.update_reviewer_state()
        obj = models.Review.objects.get(pk=obj.pk)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        msg = models.Message.objects.get(review=obj, receipient=obj.creator)
        self.assertEqual(msg.title, '"{}" is back Under Review'.format(obj.title))
        self.assertTrue(changed)
        self.assertEqual(new_state, models.reviews.REVIEWING)

    def test_update_reviewer_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        changed, new_state = obj.update_reviewer_state()
        self.assertFalse(changed)
        self.assertEqual(new_state, '')

    def test_review_state_unchanged(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        self.assertFalse(obj.update_state(models.reviews.OPEN))

    def test_review_state_change_closed(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
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

    def test_review_state_change_aborted(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
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

    def test_review_state_change_closed_to_open(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.state = models.reviews.CLOSED
        obj.save(update_fields=['state'])
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

    def test_review_state_change_aborted_to_open(self):
        obj = models.Review.create_review(**self.default_review_kwargs)
        obj.state = models.reviews.ABORTED
        obj.save(update_fields=['state'])
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

    def test_create_comment_thread(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.CommentThread.create_comment_thread(review.revision)

    def test_create_comment(self):
        self.assertEqual(models.Message.objects.count(), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachment=File(BytesIO('test_file_1')),
            attachment_type='photo',
            description='Test Description',
        )
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.attachment_type, 'photo')
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )

    def test_create_comment_with_thread(self):
        self.assertEqual(models.Message.objects.count(), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        thread = models.CommentThread.create_comment_thread(review.revision)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachment=File(BytesIO('test_file_1')),
            attachment_type='photo',
            description='Test Description',
            thread=thread,
        )
        self.assertEqual(comment.thread, thread)
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.attachment_type, 'photo')
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )

    def test_create_message(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        msg = models.Message.create_message(
            receipient=self.user,
            sender=self.system_user,
            title='Test Title',
            review_revision=review.revision,
            thread=None,
            message='Test Message'
        )
        self.assertEqual(msg.receipient, self.user)
        self.assertEqual(msg.sender, self.system_user)
        self.assertEqual(msg.review, review.revision)
        self.assertEqual(msg.title, 'Test Title')
        self.assertEqual(msg.message, 'Test Message')
