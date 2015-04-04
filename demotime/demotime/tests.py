from StringIO import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import BytesIO, File

from demotime import models


class BaseTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        for x in range(0, 3):
            User.objects.create_user(username='test_user_{}'.format(x))

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
            'reviewers': User.objects.exclude(username=self.user.username),
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

    def test_create_comment(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Test Comment',
            attachment=File(BytesIO('test_file_1')),
            attachment_type='photo',
        )
        self.assertEqual(comment.review, review.revision)
        self.assertEqual(comment.attachments.count(), 1)
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Test Comment')


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
            reviewers=User.objects.exclude(username=self.user.username),
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
            'reviewers': User.objects.exclude(username=self.user.username).values_list('pk', flat=True),
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
        self.assertEqual(rev.comment_set.count(), 1)
        comment = rev.comment_set.get()
        self.assertEqual(comment.commenter, self.user)
        self.assertEqual(comment.comment, 'Oh nice demo!')
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.get()
        self.assertEqual(attachment.attachment_type, models.Attachment.PHOTO)
