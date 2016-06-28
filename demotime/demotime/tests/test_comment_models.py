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

    def test_create_comment_starting_with_mention(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="@test_user_1 check this out with @test_user_2",
            thread=thread
        )
        self.assertEqual(models.Message.objects.count(), 2)
        test_user_1, test_user_2 = models.UserProxy.objects.filter(
            username__in=('test_user_1', 'test_user_2')
        )
        self.assertEqual(
            models.Message.objects.filter(receipient=test_user_1).count(),
            1
        )
        self.assertEqual(
            models.Message.objects.filter(receipient=test_user_2).count(),
            1
        )

    def test_create_comment_with_mention_in_middle_non_reviewer(self):
        ''' Everyone still gets mentioned, but this is a great way to include
        people otherwise not on the demo.
        '''
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        review.reviewer_set.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="Hey, do you think @test_user_1 and @test_user_2 should see this?",
            thread=thread
        )
        # Followers 1/2, Test Users 1/2
        self.assertEqual(models.Message.objects.count(), 4)
        test_user_1, test_user_2 = models.UserProxy.objects.filter(
            username__in=('test_user_1', 'test_user_2')
        )
        self.assertEqual(
            models.Message.objects.filter(receipient=test_user_1).count(),
            1
        )
        self.assertEqual(
            models.Message.objects.filter(receipient=test_user_2).count(),
            1
        )
