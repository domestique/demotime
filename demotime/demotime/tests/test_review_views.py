from StringIO import StringIO

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import models
from demotime.tests import BaseTestCase


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
