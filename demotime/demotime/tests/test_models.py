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
        )
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
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
            thread=thread,
        )
        self.assertEqual(comment.thread, thread)
        self.assertEqual(comment.thread.review_revision, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
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
