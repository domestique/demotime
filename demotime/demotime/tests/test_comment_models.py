from mock import patch

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestCommentModels(BaseTestCase):

    def setUp(self):
        super(TestCommentModels, self).setUp()
        task_patch = patch('demotime.tasks.fire_webhook')
        self.task_patch = task_patch.start()
        self.addCleanup(task_patch.stop)
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.hook = models.WebHook.objects.create(
            project=self.review.project,
            trigger_event=constants.COMMENT,
            target='http://www.example.com'
        )
        # All the tests expect a clean slate of messages
        models.Message.objects.all().delete()

    def test_create_comment_thread(self):
        thread = models.CommentThread.create_comment_thread(self.review.revision)
        self.assertEqual(thread.review_revision, self.review.revision)
        self.assertEqual(
            thread.__str__(),
            'Comment Thread for Review: {}'.format(self.review.revision)
        )

    def test_create_comment(self):
        self.assertEqual(models.Message.objects.count(), 0)
        models.UserReviewStatus.objects.filter(review=self.review).update(read=True)
        attachments = [
            {
                'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'description': 'Image 1',
            },
            {
                'attachment': File(BytesIO(b'test_file_2'), name='test_file_2.jpg'),
                'description': 'Image 2',
            },
        ]
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachments=attachments,
        )
        self.assertEqual(
            comment.get_absolute_url(),
            '{}#{}'.format(
                reverse('review-rev-detail', kwargs={
                    'proj_slug': self.review.project.slug,
                    'pk': self.review.pk,
                    'rev_num': self.review.revision.number,
                }),
                comment.pk
            )
        )
        self.assertEqual(comment.thread.review_revision, self.review.revision)
        self.assertEqual(comment.attachments.count(), 2)
        attachment_one, attachment_two = comment.attachments.all()
        self.assertEqual(attachment_one.description, 'Image 1')
        self.assertEqual(attachment_one.attachment_type, 'image')
        self.assertEqual(attachment_one.sort_order, 0)
        self.assertEqual(attachment_two.description, 'Image 2')
        self.assertEqual(attachment_two.attachment_type, 'image')
        self.assertEqual(attachment_two.sort_order, 1)
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            5
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        statuses = models.UserReviewStatus.objects.filter(review=self.review)
        self.assertEqual(statuses.count(), 6)
        self.assertEqual(statuses.filter(read=True).count(), 1)
        self.assertEqual(statuses.filter(read=False).count(), 5)
        self.assertEqual(
            comment.__str__(),
            'Comment by {} on Review: {}'.format(
                comment.commenter.username,
                self.review.title
            )
        )
        self.task_patch.delay.assert_called_with(
            self.review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_create_comment_with_thread(self):
        self.assertEqual(models.Message.objects.count(), 0)
        review = models.Review.create_review(**self.default_review_kwargs)
        thread = models.CommentThread.create_comment_thread(review.revision)
        models.UserReviewStatus.objects.filter(review=review).update(read=True)
        attachments = [{
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'sort_order': 1,
            'description': 'Test Description'
        }]
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachments=attachments,
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
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)
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
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="<p></p>@test_user_1 check this out with @test_user_2</p><br>",
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
        self.task_patch.delay.assert_called_with(
            review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_create_comment_with_mention_in_middle_non_reviewer(self):
        ''' Everyone still gets mentioned, but this is a great way to include
        people otherwise not on the demo.
        '''
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        review.reviewer_set.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="<br><p>Hey, do you think @test_user_1 and @test_user_2 should see this?</p><br>",
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
        self.task_patch.delay.assert_called_with(
            review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_create_comment_mention_missing_user(self):
        ''' If a comment starts with a missing user, we should ignore the
        mention and follow our normal comment emailing rules
        '''
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="<p></p>@not_real check this out with @so_not_real</p><br>",
            thread=thread
        )
        # 3 reviewers, 2 followers, commenter was creator
        self.assertEqual(models.Message.objects.count(), 5)
        self.task_patch.delay.assert_called_with(
            review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_create_comment_case_insensitive_mentions(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="<p></p>@TEST_USER_1 check this out with @TeSt_UsEr_2</p><br>",
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
        self.task_patch.delay.assert_called_with(
            review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_create_comment_mention_ignores_misses(self):
        ''' If a username is bad within a comment with a mention, we still hit
        the other mentions
        '''
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="<p></p>@test_user_1 check this out with @BAD_USERNAME</p><br>",
            thread=thread
        )
        self.assertEqual(models.Message.objects.count(), 1)
        test_user_1 = models.UserProxy.objects.get(username='test_user_1')
        self.assertEqual(
            models.Message.objects.filter(receipient=test_user_1).count(),
            1
        )
        self.task_patch.delay.assert_called_with(
            review.pk,
            self.hook.pk,
            {'comment': comment.to_json()},
        )
        event = comment.events.get()
        self.assertEqual(event.event_type.code, event.event_type.COMMENT_ADDED)
        self.assertEqual(event.related_object, comment)
        self.assertEqual(event.user, comment.commenter)

    def test_comment_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        models.Message.objects.all().delete()
        self.assertEqual(models.Message.objects.count(), 0)
        thread = models.CommentThread.create_comment_thread(review.revision)
        attachments = [{
            'attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
            'sort_order': 1,
            'description': 'Test Description'
        }]
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment="test comment",
            thread=thread,
            attachments=attachments,
        )
        self.assertEqual(comment.to_json(), {
            'id': comment.pk,
            'thread': comment.thread.pk,
            'name': comment.commenter.userprofile.name,
            'comment': comment.comment,
            'attachment_count': comment.attachments.count(),
            'attachments': [comment.attachments.get().to_json()],
            'url': comment.get_absolute_url(),
            'thread_url': comment.get_absolute_thread_url(),
            'created': comment.created.isoformat(),
            'modified': comment.modified.isoformat(),
        })
