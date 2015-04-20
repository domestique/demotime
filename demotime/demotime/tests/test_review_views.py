import json
from StringIO import StringIO

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import BytesIO, File

from demotime import models
from demotime.tests import BaseTestCase


class TestReviewViews(BaseTestCase):

    def setUp(self):
        super(TestReviewViews, self).setUp()
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
                    'description': 'Testing',
                },
                {
                    'attachment': File(BytesIO('test_file_2')),
                    'attachment_type': 'photo',
                    'description': 'Testing',
                },
            ],
        )
        # Reset out mail queue
        mail.outbox = []

    def test_get_index(self):
        response = self.client.get(reverse('index'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'demotime/index.html')
        for key in ['open_demos', 'open_reviews', 'updated_demos']:
            assert key in response.context

    def test_get_review_detail(self):
        models.UserReviewStatus.objects.filter(
            review=self.review,
            user=self.user
        ).update(read=False)
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)
        self.assertTemplateUsed(response, 'demotime/review.html')
        # We're the creator, not a reviewer
        self.assertNotIn('reviewer', response.context)
        self.assertNotIn('reviewer_status_form', response.context)
        self.assertIn('review_state_form', response.context)
        review_state_form = response.context['review_state_form']
        self.assertEqual(review_state_form.initial['review'], self.review)
        user_review_status = models.UserReviewStatus.objects.get(
            review=self.review,
            user=self.user
        )
        self.assertTrue(user_review_status.read)

    def test_get_review_detail_as_reviewer(self):
        self.client.logout()
        self.client.login(username='test_user_0', password='testing')
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)
        self.assertTemplateUsed(response, 'demotime/review.html')
        # We're the reviewer
        self.assertIn('reviewer', response.context)
        self.assertIn('reviewer_status_form', response.context)
        reviewer_form = response.context['reviewer_status_form']
        self.assertTrue(reviewer_form.fields['reviewer'].queryset.filter(
            reviewer__username='test_user_0'
        ).exists())
        self.assertEqual(reviewer_form.initial['review'], self.review)

    def test_get_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 302)

    def test_review_rev_detail(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'pk': self.review.pk,
            'rev_pk': self.review.revision.pk
        }))
        self.assertStatusCode(response, 200)

    def test_review_rev_detail_404(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'pk': self.review.pk,
            'rev_pk': 500,
        }))
        self.assertStatusCode(response, 404)

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
        self.assertEqual(len(mail.outbox), 0)
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
            'form-0-description': 'Test Description',
        })
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.case_link, 'http://www.example.org')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.revision.attachments.count(), 1)
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'photo')
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(
            models.Message.objects.filter(title__contains='POST').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        self.assertEqual(len(mail.outbox), 3)

    def test_post_update_review(self):
        fh = StringIO('testing')
        fh.name = 'test_file_1'
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
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
            'form-0-description': 'Test Description',
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
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'photo')
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(
            models.Message.objects.filter(title__contains='Update Review POST').count(),
            3
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        self.assertEqual(len(mail.outbox), 3)

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

    def test_update_reviewer_status(self):
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        url = reverse(
            'update-reviewer-status', args=[self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': models.reviews.APPROVED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewer_state_changed': False,
            'new_state': '',
            'reviewer_status': models.reviews.APPROVED,
            'success': True,
            'errors': {},
        })

    def test_update_reviewer_status_failure(self):
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        url = reverse(
            'update-reviewer-status', args=[self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': 'BOGUS',
        })
        self.assertStatusCode(response, 400)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewer_state_changed': False,
            'new_state': '',
            'reviewer_status': reviewer.status,
            'success': False,
            'errors': {
                'status': [u'Select a valid choice. BOGUS is not one of the available choices.'],
            },
        })

    def test_update_reviewer_status_state_change(self):
        self.assertEqual(len(mail.outbox), 0)
        self.review.reviewer_set.update(status=models.reviews.APPROVED)
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        reviewer.status = models.reviews.REVIEWING
        reviewer.save(update_fields=['status'])
        reviewer = models.Reviewer.objects.get(pk=reviewer.pk)
        self.assertEqual(self.review.reviewer_state, models.reviews.REVIEWING)
        self.assertEqual(reviewer.status, models.reviews.REVIEWING)
        url = reverse('update-reviewer-status', kwargs={
            'review_pk': self.review.pk, 'reviewer_pk': reviewer.pk
        })
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': models.reviews.APPROVED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'reviewer_state_changed': True,
            'new_state': models.reviews.APPROVED,
            'reviewer_status': models.reviews.APPROVED,
            'success': True,
            'errors': {},
        })
        self.assertEqual(len(mail.outbox), 1)

    def test_update_reviewer_status_failure_wrong_user(self):
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=self.test_users[0],
        )
        url = reverse(
            'update-reviewer-status', args=[self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': 'BOGUS',
        })
        self.assertStatusCode(response, 404)

    def test_update_review_state_closed(self):
        self.assertEqual(len(mail.outbox), 0)
        url = reverse('update-review-state', args=[self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': models.reviews.CLOSED
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'state': models.reviews.CLOSED,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        title = '"{}" has been Closed'.format(self.review.title)
        self.assertEqual(
            models.Message.objects.filter(title=title).count(),
            3
        )
        self.assertEqual(len(mail.outbox), 3)

    def test_update_review_state_aborted(self):
        url = reverse('update-review-state', args=[self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': models.reviews.ABORTED
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'state': models.reviews.ABORTED,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        title = '"{}" has been Aborted'.format(self.review.title)
        self.assertEqual(
            models.Message.objects.filter(title=title).count(),
            3
        )

    def test_update_review_state_reopened(self):
        self.review.state = models.reviews.CLOSED
        self.review.save(update_fields=['state'])
        url = reverse('update-review-state', args=[self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': models.reviews.OPEN,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'state': models.reviews.OPEN,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        title = '"{}" has been Reopened'.format(self.review.title)
        self.assertEqual(
            models.Message.objects.filter(title=title).count(),
            3
        )

    def test_update_review_state_invalid(self):
        self.client.logout()
        self.client.login(username='test_user_0', password='testing')
        url = reverse('update-review-state', args=[self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': models.reviews.OPEN,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content), {
            'state': self.review.state,
            'state_changed': False,
            'success': False,
            'errors': {
                'review': ['Select a valid choice. That choice is not one of the available choices.']
            },
        })
