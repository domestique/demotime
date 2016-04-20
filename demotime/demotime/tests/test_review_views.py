import json
from StringIO import StringIO

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

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
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Reset out mail queue
        mail.outbox = []

    def test_get_index(self):
        followed_kwargs = self.default_review_kwargs.copy()
        followed_kwargs['creator'] = self.test_users[0]
        followed_kwargs['reviewers'] = self.test_users.exclude(pk=self.test_users[0].pk)
        followed_kwargs['followers'] = [self.user]
        followed_review = models.Review.create_review(**followed_kwargs)

        reviewer_kwargs = self.default_review_kwargs.copy()
        reviewer_kwargs['creator'] = self.test_users[0]
        reviewer_kwargs['followers'] = self.test_users.exclude(pk=self.test_users[0].pk)
        reviewer_kwargs['reviewers'] = [self.user]
        reviewer_review = models.Review.create_review(**reviewer_kwargs)

        response = self.client.get(reverse('index'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'demotime/index.html')
        for key in ['open_demos', 'open_reviews', 'updated_demos', 'message_bundles', 'followed_demos']:
            assert key in response.context

        self.assertIn(followed_review, response.context['followed_demos'])
        self.assertIn(self.review, response.context['open_demos'])
        self.assertIn(reviewer_review, response.context['open_reviews'])
        self.assertEqual(
            list(response.context['updated_demos'].values_list('pk', flat=True)),
            list(models.UserReviewStatus.objects.filter(user=self.user).values_list('pk', flat=True))
        )
        self.assertEqual(models.Review.objects.count(), 3)
        self.assertEqual(len(response.context['message_bundles']), 2)

    def test_get_review_detail(self):
        models.UserReviewStatus.objects.filter(
            review=self.review,
            user=self.user
        ).update(read=False)
        bundle, _ = models.MessageBundle.objects.get_or_create(
            review=self.review,
            owner=self.user
        )
        bundle.read = False
        bundle.deleted = False
        bundle.save()
        self.assertTrue(
            models.MessageBundle.objects.filter(
                review=self.review,
                owner=self.user,
                read=False,
                deleted=False,
            ).exists()
        )
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
        self.assertFalse(
            models.MessageBundle.objects.filter(
                review=self.review,
                owner=self.user,
                read=False,
                deleted=False,
            ).exists()
        )

    def test_get_review_detail_as_reviewer(self):
        self.client.logout()
        user = User.objects.get(username='test_user_0')
        self.client.login(username=user.username, password='testing')
        bundle, _ = models.MessageBundle.objects.get_or_create(
            review=self.review,
            owner=user
        )
        bundle.read = False
        bundle.deleted = False
        bundle.save()
        self.assertTrue(
            models.MessageBundle.objects.filter(
                review=self.review,
                owner=user,
                read=False,
                deleted=False,
            ).exists()
        )
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
        self.assertFalse(
            models.MessageBundle.objects.filter(
                review=self.review,
                owner=self.user,
                read=False,
                deleted=False,
            ).exists()
        )

    def test_get_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('review-detail', args=[self.review.pk]))
        self.assertStatusCode(response, 302)

    def test_review_rev_detail(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'pk': self.review.pk,
            'rev_num': self.review.revision.number,
        }))
        self.assertStatusCode(response, 200)

    def test_review_rev_detail_404(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'pk': self.review.pk,
            'rev_num': 500,
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
            'followers': self.followers.values_list('pk', flat=True),
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 5,
            'form-0-attachment': fh,
            'form-0-attachment_type': 'image',
            'form-0-description': 'Test Description',
        })
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description'),
        self.assertEqual(obj.case_link, 'http://www.example.org')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.followers.count(), 2)
        self.assertEqual(obj.revision.attachments.count(), 1)
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'image')
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(
            models.Message.objects.filter(title__contains='POST').count(),
            5
        )
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertFalse(
            models.Message.objects.filter(receipient=self.user).exists()
        )
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

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
            'followers': [],
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 5,
            'form-0-attachment': fh,
            'form-0-attachment_type': 'image',
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
        self.assertEqual(obj.followers.count(), 0)
        self.assertEqual(obj.revision.attachments.count(), 1)
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'image')
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
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
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
        # Only one message, simply for the approval
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
            5
        )
        self.assertEqual(len(mail.outbox), 5)

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
            5
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
            5
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

    def test_review_list(self):
        response = self.client.get(reverse('review-list'))
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_creator(self):
        response = self.client.get(reverse('review-list'), {
            'creator': self.user.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.creator, self.user)

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'creator': User.objects.get(username='test_user_0').pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_reviewer(self):
        test_user = User.objects.get(username='test_user_0')
        response = self.client.get(reverse('review-list'), {
            'reviewer': test_user.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.creator, self.user)
        self.assertIn(test_user, obj.reviewers.all())

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'reviewer': self.user.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_state(self):
        response = self.client.get(reverse('review-list'), {
            'state': models.reviews.OPEN,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, models.reviews.OPEN)

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'state': models.reviews.CLOSED,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_reviewer_state(self):
        response = self.client.get(reverse('review-list'), {
            'reviewer_state': models.reviews.REVIEWING,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, models.reviews.OPEN)

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'reviewer_state': models.reviews.APPROVED,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_search_title(self):
        response = self.client.get(reverse('review-list'), {
            'title': 'test'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.title, 'Test Title')

        # Bad Search
        response = self.client.get(reverse('review-list'), {
            'title': 'IASIP'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_review_list_all_the_filters(self):
        test_user = User.objects.get(username='test_user_0')
        response = self.client.get(reverse('review-list'), {
            'reviewer': test_user.pk,
            'creator': self.user.pk,
            'state': models.reviews.OPEN,
            'reviewer_state': models.reviews.REVIEWING,
            'title': 'test',
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, models.reviews.OPEN)
        self.assertEqual(obj.creator, self.user)
        self.assertEqual(obj.reviewer_state, models.reviews.REVIEWING)
        self.assertIn(test_user, obj.reviewers.all())
        self.assertEqual(obj.title, 'Test Title')

    def test_review_json_no_match(self):
        response = self.client.post(reverse('reviews-json'), {
            'title': 'zxy'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'count': 0,
            'reviews': []
        })

    def test_review_json_by_pk(self):
        response = self.client.post(reverse('reviews-json'), {
            'pk': self.review.pk,
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        self.assertEqual(review['title'], self.review.title)
        self.assertEqual(review['pk'], self.review.pk)
        self.assertEqual(review['url'], self.review.get_absolute_url())
        self.assertEqual(review['reviewing_count'], 3)
        self.assertEqual(review['approved_count'], 0)
        self.assertEqual(review['rejected_count'], 0)
        reviewers = json_data['reviews'][0]['reviewers']
        followers = json_data['reviews'][0]['followers']
        for follower in self.followers:
            self.assertIn(
                {'user_pk': follower.pk, 'name': follower.userprofile.name},
                followers
            )
        for reviewer in self.test_users:
            self.assertIn(
                {
                    'user_pk': reviewer.pk,
                    'name': reviewer.userprofile.name,
                    'reviewer_status': models.reviews.REVIEWING,
                },
                reviewers
            )

    def test_review_json_all_the_filters(self):
        test_user = User.objects.get(username='test_user_0')
        response = self.client.post(reverse('reviews-json'), {
            'reviewer': test_user.pk,
            'creator': self.user.pk,
            'state': models.reviews.OPEN,
            'reviewer_state': models.reviews.REVIEWING,
            'title': 'test',
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        review_obj = models.Review.objects.get(pk=review['pk'])
        self.assertEqual(review['title'], 'Test Title')
        self.assertEqual(review['creator'], self.user.userprofile.name)
        self.assertEqual(review['state'], models.reviews.OPEN)
        self.assertEqual(review['reviewer_state'], models.reviews.REVIEWING)
        self.assertEqual(review['url'], review_obj.get_absolute_url())
        reviewers = review['reviewers']
        self.assertIn(test_user.pk, [x['user_pk'] for x in reviewers])

    def test_review_list_sort_by_newest(self):
        review_kwargs = self.default_review_kwargs.copy()
        review_kwargs['title'] = 'Newer Review'
        newer_review = models.Review.create_review(**review_kwargs)
        response = self.client.get(reverse('review-list'), {
            'sort_by': 'newest'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.pk, newer_review.pk)

    def test_review_list_sort_by_oldest(self):
        self.default_review_kwargs['title'] = 'Newer Review'
        models.Review.create_review(**self.default_review_kwargs)
        response = self.client.get(reverse('review-list'), {
            'sort_by': 'oldest'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.pk, self.review.pk)

    def test_review_redirect_view(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        response = self.client.get(
            reverse('dt-redirect', kwargs={'pk': review.pk})
        )
        self.assertStatusCode(response, 301)
        self.assertRedirects(
            response,
            reverse('review-detail', kwargs={'pk': review.pk}),
            status_code=301,
        )

    def test_review_redirect_view_not_found(self):
        self.assertFalse(models.Review.objects.filter(pk=10000).exists())
        response = self.client.get(
            reverse('dt-redirect', kwargs={'pk': 10000})
        )
        self.assertStatusCode(response, 404)
