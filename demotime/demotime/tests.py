from StringIO import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import BytesIO, File

from demotime import models


class BaseTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.system_user = User.objects.get(username='demotime_sys')
        for x in range(0, 3):
            User.objects.create_user(username='test_user_{}'.format(x))

        self.test_users = User.objects.filter(username__startswith="test_user_")

    def assertStatusCode(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)


class TestReviewModels(BaseTestCase):

    def setUp(self):
        super(TestReviewModels, self).setUp()
        self.default_review_kwargs = {
            'creator': self.user,
            'title': 'Test Title',
            'description': 'Test Description',
            'case_link': 'http://example.org/',
            'reviewers': self.test_users,
            'attachments': [
                {
                    'attachment': File(BytesIO('test_file_1')),
                    'attachment_type': 'photo',
                },
                {
                    'attachment': File(BytesIO('test_file_2')),
                    'attachment_type': 'photo',
                },
            ],
        }

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


class TestReviewViews(BaseTestCase):

    def setUp(self):
        super(TestReviewViews, self).setUp()
        self.user.set_password('testing')
        self.user.save()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        # Sample review
        self.review = models.Review.create_review(
            creator=self.user,
            title='Test Title',
            description='Test Description',
            case_link='http://example.org/',
            reviewers=self.test_users,
            attachments=[
                {
                    'attachment': File(BytesIO('test_file_1')),
                    'attachment_type': 'photo',
                },
                {
                    'attachment': File(BytesIO('test_file_2')),
                    'attachment_type': 'photo',
                },
            ],
        )

    def test_get_index(self):
        response = self.client.get(reverse('index'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'demotime/index.html')
        for key in ['open_demos', 'open_reviews', 'updated_demos']:
            assert key in response.context

    def test_get_review_detail(self):
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)
        self.assertTemplateUsed(response, 'demotime/review.html')

    def test_get_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 302)

    def test_get_create_review(self):
        response = self.client.get(reverse('create-review'))
        self.assertStatusCode(response, 200)
        self.assertIn('review_form', response.context)
        self.assertIn('review_inst', response.context)
        self.assertIn('attachment_forms', response.context)

    def test_get_create_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('create-review'))
        self.assertStatusCode(response, 302)

    def test_post_create_review(self):
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        title = 'Test Title Create Review POST'
        response = self.client.post(reverse('create-review'), {
            'creator': self.user,
            'title': title,
            'description': 'Test Description',
            'case_link': 'http://www.example.org',
            'reviewers': self.test_users.values_list('pk', flat=True),
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 5,
            'form-0-attachment': fh,
            'form-0-attachment_type': 'photo',
        })
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.case_link, 'http://www.example.org')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 1)
        self.assertEqual(
            models.Message.objects.filter(title__contains='POST').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )

    def test_post_update_review(self):
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        title = 'Test Title Update Review POST'
        response = self.client.post(reverse('edit-review', args=[self.review.pk]), {
            'creator': self.user,
            'title': title,
            'description': 'Updated Description',
            'case_link': 'http://www.example.org/1/',
            'reviewers': self.test_users.values_list('pk', flat=True),
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 5,
            'form-0-attachment': fh,
            'form-0-attachment_type': 'photo',
        })
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.revision.description, 'Updated Description'),
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 1)
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(
            models.Message.objects.filter(title__contains='Update Review POST').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )

    def test_post_create_review_with_errors(self):
        response = self.client.post(reverse('create-review'), {
            'creator': self.user,
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 5,
        })
        self.assertStatusCode(response, 200)
        form = response.context['review_form']
        self.assertIn('title', form.errors)

    def test_comment_on_review(self):
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
            'attachment': fh,
            'attachment_type': 'photo',
        })
        self.assertStatusCode(response, 302)
        rev = self.review.revision
        self.assertEqual(rev.commentthread_set.count(), 1)
        self.assertEqual(
            rev.commentthread_set.get().comment_set.count(),
            1
        )
        comment = rev.commentthread_set.get().comment_set.get()
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Oh nice demo!')
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.attachment_type, models.Attachment.PHOTO)
        self.assertEqual(
            models.Message.objects.filter(title__contains='New Comment').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )

    def test_reply_to_comment(self):
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
        })
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 1)

        thread = rev.commentthread_set.get()
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Reply!",
            'thread': thread.pk
        })
        self.assertStatusCode(response, 302)
        # Still just 1 thread
        self.assertEqual(rev.commentthread_set.count(), 1)
        self.assertEqual(thread.comment_set.count(), 2)
        self.assertTrue(thread.comment_set.filter(comment='Reply!').exists())

    def test_create_second_thread(self):
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "Oh nice demo!",
        })
        rev = self.review.revision
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 1)

        thread = rev.commentthread_set.get()
        response = self.client.post(reverse('review-detail', args=[self.review.pk]), {
            'comment': "New Comment!",
        })
        self.assertStatusCode(response, 302)
        self.assertEqual(rev.commentthread_set.count(), 2)
        self.assertEqual(thread.comment_set.count(), 1)
        self.assertFalse(
            thread.comment_set.filter(comment='New Comment!').exists()
        )

        new_thread = rev.commentthread_set.latest()
        self.assertTrue(
            new_thread.comment_set.filter(comment='New Comment!').exists()
        )
