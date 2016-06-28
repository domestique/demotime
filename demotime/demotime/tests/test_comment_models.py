from django.core.files.uploadedfile import BytesIO, File

from demotime import models
from demotime.tests import BaseTestCase


class TestCommentModels(BaseTestCase):

    def test_create_comment_thread(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        thread = models.CommentThread.create_comment_thread(review.revision)
        self.assertEqual(thread.review_revision, review.revision)
        self.assertEqual(
            thread.__str__(),
            'Comment Thread for Review: {}'.format(review.revision)
        )

    def test_create_comment(self):
        self.assertEqual(models.Message.objects.count(), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        models.UserReviewStatus.objects.filter(review=review).update(read=True)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachment=File(BytesIO(b'test_file_1')),
            attachment_type='image',
            description='Test Description',
        )
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.attachment_type, 'image')
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            5
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        statuses = models.UserReviewStatus.objects.filter(review=review)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(
            comment.__str__(),
            'Comment by {} on Review: {}'.format(
                comment.commenter.username,
                review.title
            )
        )

    def test_create_comment_with_thread(self):
        self.assertEqual(models.Message.objects.count(), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        thread = models.CommentThread.create_comment_thread(review.revision)
        models.UserReviewStatus.objects.filter(review=review).update(read=True)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachment=File(BytesIO(b'test_file_1')),
            attachment_type='image',
            description='Test Description',
            thread=thread,
        )
        self.assertEqual(comment.thread, thread)
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.attachment_type, 'image')
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            5
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        statuses = models.UserReviewStatus.objects.filter(review=review)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
