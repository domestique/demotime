import json

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.files.uploadedfile import BytesIO, File

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReviewViews(BaseTestCase):  # pylint: disable=too-many-public-methods

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
        draft_kwargs = self.default_review_kwargs.copy()
        draft_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**draft_kwargs)

        paused_review = models.Review.create_review(**self.default_review_kwargs)
        paused_review.update_state(constants.PAUSED)
        paused_review.refresh_from_db()

        followed_kwargs = self.default_review_kwargs.copy()
        followed_kwargs['creators'] = [self.test_users[0]]
        followed_kwargs['reviewers'] = self.test_users.exclude(
            pk=self.test_users[0].pk
        )
        followed_kwargs['followers'] = [self.user]
        followed_review = models.Review.create_review(**followed_kwargs)

        reviewer_kwargs = self.default_review_kwargs.copy()
        reviewer_kwargs['creators'] = [self.test_users[0]]
        reviewer_kwargs['followers'] = self.test_users.exclude(
            pk=self.test_users[0].pk
        )
        reviewer_kwargs['reviewers'] = [self.user]
        reviewer_review = models.Review.create_review(**reviewer_kwargs)

        deleted_reviewer_kwargs = self.default_review_kwargs.copy()
        deleted_reviewer_kwargs['reviewers'] = [self.user]
        deleted_reviewer_kwargs['creators'] = [self.test_users[0]]
        deleted_reviewer_review = models.Review.create_review(
            **deleted_reviewer_kwargs
        )
        deleted_reviewer = deleted_reviewer_review.reviewer_set.active()[0]
        deleted_reviewer.drop_reviewer(
            deleted_reviewer_review.creator_set.active().get().user
        )

        deleted_follower_kwargs = self.default_review_kwargs.copy()
        deleted_follower_kwargs['followers'] = [self.user]
        deleted_follower_kwargs['creators'] = [self.followers[0]]
        deleted_follower_review = models.Review.create_review(
            **deleted_follower_kwargs
        )
        deleted_follower = deleted_follower_review.follower_set.active()[0]
        deleted_follower.drop_follower(
            deleted_follower_review.creator_set.active().get().user
        )

        response = self.client.get(reverse('index'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'demotime/index.html')
        for key in ['open_demos', 'paused_demos', 'open_reviews',
                    'drafts', 'followed_demos']:
            self.assertIn(key, response.context)

        self.assertIn(followed_review, response.context['followed_demos'])
        self.assertNotIn(deleted_follower_review, response.context['followed_demos'])
        self.assertIn(self.review, response.context['open_demos'])
        self.assertIn(reviewer_review, response.context['open_reviews'])
        self.assertNotIn(deleted_reviewer_review, response.context['open_reviews'])
        self.assertIn(draft_review, response.context['drafts'])
        self.assertIn(paused_review, response.context['paused_demos'])
        self.assertEqual(models.Review.objects.count(), 7)

    def test_index_does_hide_approved_reviews_from_open_reviews(self):
        review_one_kwargs = self.default_review_kwargs.copy()
        review_one_kwargs['creators'] = [self.test_users[0]]
        review_one_kwargs['reviewers'] = [self.user]
        review_one = models.Review.create_review(**review_one_kwargs)

        review_two_kwargs = self.default_review_kwargs.copy()
        review_two_kwargs['creators'] = [self.test_users[0]]
        review_two_kwargs['reviewers'] = [self.user]
        review_two = models.Review.create_review(**review_two_kwargs)

        models.Reviewer.objects.filter(
            reviewer=self.user,
            review=review_two
        ).update(status=constants.APPROVED)

        response = self.client.get(reverse('index'))
        self.assertStatusCode(response, 200)
        open_reviews = response.context['open_reviews']
        self.assertEqual(len(open_reviews), 1)
        # Newest review first
        self.assertEqual(open_reviews[0].pk, review_one.pk)

    def test_get_review_detail(self):
        models.UserReviewStatus.objects.filter(
            review=self.review,
            user=self.user
        ).update(read=False)
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)
        self.assertTemplateUsed(response, 'demotime/review.html')
        # We're the creator, not a reviewer
        self.assertNotIn('reviewer', response.context)
        self.assertNotIn('reviewer_status_form', response.context)
        self.assertIn('review_state_form', response.context)
        self.assertEqual(response.context['creator_obj'].user, self.user)
        review_state_form = response.context['review_state_form']
        self.assertEqual(review_state_form.initial['review'], self.review)
        user_review_status = models.UserReviewStatus.objects.get(
            review=self.review,
            user=self.user
        )
        self.assertTrue(user_review_status.read)

    def test_review_detail_hides_inactive_reviewer_followers(self):
        reviewer = self.review.reviewer_set.active()[0]
        follower = self.review.follower_set.active()[0]
        reviewer.drop_reviewer(self.review.creator_set.active().get().user)
        follower.drop_follower(self.review.creator_set.active().get().user)
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 200)
        self.assertNotIn(
            reviewer.reviewer.userprofile.name,
            response.content.decode('utf-8')
        )
        self.assertNotIn(
            follower.user.userprofile.name,
            response.content.decode('utf-8')
        )

    def test_get_draft_review_as_creator(self):
        self.review.state = constants.DRAFT
        self.review.save(update_fields=['state'])
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)

    def test_get_draft_review_not_creator(self):
        self.client.logout()
        user = User.objects.get(username='test_user_0')
        self.client.login(username=user.username, password='testing')
        self.review.state = constants.DRAFT
        self.review.save(update_fields=['state'])
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 403)

    def test_get_review_detail_as_reviewer(self):
        self.client.logout()
        user = User.objects.get(username='test_user_0')
        self.client.login(username=user.username, password='testing')
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['object'].pk, self.review.pk)
        self.assertTemplateUsed(response, 'demotime/review.html')
        # We're the reviewer
        self.assertIn('reviewer', response.context)
        reviewer = response.context['reviewer']
        reviewer.refresh_from_db()
        self.assertEqual(reviewer.last_viewed.date(), timezone.now().date())
        self.assertIn('reviewer_status_form', response.context)
        self.assertIsNone(response.context['creator_obj'])
        reviewer_form = response.context['reviewer_status_form']
        self.assertTrue(reviewer_form.fields['reviewer'].queryset.filter(
            reviewer__username='test_user_0'
        ).exists())
        self.assertEqual(reviewer_form.initial['review'], self.review)

    def test_get_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse(
            'review-detail',
            args=[self.project.slug, self.review.pk]
        ))
        self.assertStatusCode(response, 302)

    def test_review_rev_detail(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'proj_slug': self.project.slug,
            'pk': self.review.pk,
            'rev_num': self.review.revision.number,
        }))
        self.assertStatusCode(response, 200)

    def test_review_rev_detail_404(self):
        response = self.client.get(reverse('review-rev-detail', kwargs={
            'proj_slug': self.project.slug,
            'pk': self.review.pk,
            'rev_num': 500,
        }))
        self.assertStatusCode(response, 302)
        self.assertRedirects(
            response,
            reverse('review-rev-detail', kwargs={
                'proj_slug': self.project.slug,
                'pk': self.review.pk,
                'rev_num': self.review.revision.number,
            })
        )

    def test_get_create_review(self):
        response = self.client.get(reverse('create-review', args=[self.project.slug]))
        self.assertStatusCode(response, 302)
        new_review = models.Review.objects.first()
        self.assertRedirects(response, reverse(
            'edit-review', kwargs={
                'proj_slug': self.project.slug,
                'pk': new_review.pk
            }
        ))
        self.assertEqual(
            new_review.creator_set.active().get().user,
            self.user
        )
        self.assertEqual(new_review.title, '')

    def test_get_create_review_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('create-review', args=[self.project.slug]))
        self.assertStatusCode(response, 302)

    def test_edit_review_filters_out_unauthorized_users(self):
        ''' Test asserts that we don't show reviewer/followers that aren't
        part of the project that the review is being created under
        '''
        unauthed_user = User.objects.create(username='bad_user')
        response = self.client.get(
            reverse('edit-review', args=[self.project.slug, self.review.pk])
        )
        self.assertStatusCode(response, 200)
        form = response.context['review_form']
        reviewers = form.fields['reviewers'].queryset
        followers = form.fields['followers'].queryset
        self.assertNotIn(unauthed_user, reviewers)
        self.assertNotIn(unauthed_user, followers)

    def test_get_update_draft_review(self):
        reviewer = self.review.reviewer_set.all()[0]
        follower = self.review.follower_set.all()[0]
        reviewer.drop_reviewer(self.review.creator_set.active().get().user)
        follower.drop_follower(self.review.creator_set.active().get().user)
        response = self.client.get(
            reverse('edit-review', args=[self.project.slug, self.review.pk])
        )
        self.assertStatusCode(response, 200)
        review_inst = response.context['review_inst']
        self.assertEqual(review_inst, self.review)
        self.assertEqual(response.context['project'], self.review.project)
        review_form = response.context['review_form']
        self.assertEqual(review_form.instance, self.review)
        self.assertEqual(self.review.reviewer_set.active().count(), 2)
        self.assertEqual(self.review.follower_set.active().count(), 1)
        self.assertEqual(
            list(review_form.initial['reviewers']),
            list(self.review.reviewer_set.active().values_list('reviewer__pk', flat=True))
        )
        self.assertEqual(
            list(review_form.initial['followers']),
            list(self.review.follower_set.active().values_list('user__pk', flat=True))
        )

    def test_get_update_draft_review_with_coowner(self):
        reviewer = self.review.reviewer_set.all()[0]
        follower = self.review.follower_set.all()[0]
        models.Creator.create_creator(self.co_owner, self.review)
        reviewer.drop_reviewer(self.user)
        follower.drop_follower(self.user)
        response = self.client.get(
            reverse('edit-review', args=[self.project.slug, self.review.pk])
        )
        self.assertStatusCode(response, 200)
        review_inst = response.context['review_inst']
        self.assertEqual(review_inst, self.review)
        self.assertEqual(response.context['project'], self.review.project)
        review_form = response.context['review_form']
        self.assertEqual(review_form.instance, self.review)
        self.assertEqual(self.review.reviewer_set.active().count(), 2)
        self.assertEqual(self.review.follower_set.active().count(), 1)
        self.assertEqual(review_form.initial['creators'], self.co_owner.pk)
        self.assertEqual(
            list(review_form.initial['reviewers']),
            list(self.review.reviewer_set.active().values_list('reviewer__pk', flat=True))
        )
        self.assertEqual(
            list(review_form.initial['followers']),
            list(self.review.follower_set.active().values_list('user__pk', flat=True))
        )

    def test_post_update_draft_review(self):
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        draft_kwargs = self.default_review_kwargs.copy()
        draft_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**draft_kwargs)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, draft_review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.DRAFT,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
                'form-0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'form-0-description': 'Test Description',
                'form-0-sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.filter(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertFalse(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.DEMO_UPDATED
        )
        self.assertFalse(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertFalse(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertFalse(event.exists())
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        # Drafts update the Review description
        self.assertEqual(obj.description, 'Updated Description')
        self.assertEqual(obj.revision.description, 'Updated Description')
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewers.count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 0)
        self.assertEqual(obj.revision.attachments.count(), 3)
        self.assertEqual(obj.state, constants.DRAFT)

    def test_post_update_draft_review_to_open(self):
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        draft_kwargs = self.default_review_kwargs.copy()
        draft_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**draft_kwargs)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, draft_review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
                'form-0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'form-0-description': 'Test Description',
                'form-0-sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.filter(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertTrue(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.DEMO_UPDATED
        )
        self.assertFalse(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.REVIEWER_ADDED
        )
        self.assertTrue(event.exists())
        event = obj.event_set.filter(
            event_type__code=models.EventType.FOLLOWER_ADDED
        )
        self.assertFalse(event.exists())
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        # Drafts update the Review description
        self.assertEqual(obj.description, 'Updated Description')
        self.assertEqual(obj.revision.description, 'Updated Description')
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 0)
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.revision.attachments.count(), 3)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_post_update_draft_review_to_open_no_attachments(self):
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        draft_kwargs = self.default_review_kwargs.copy()
        draft_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**draft_kwargs)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, draft_review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.filter(event_type__code=models.EventType.DEMO_CREATED)
        self.assertTrue(event.exists())
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        # Drafts update the Review description
        self.assertEqual(obj.description, 'Updated Description')
        self.assertEqual(obj.revision.description, 'Updated Description')
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 0)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(
            models.UserReviewStatus.objects.filter(
                review=obj,
                read=False
            ).exclude(user=self.user).count(),
            5
        )
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_post_delete_draft(self):
        draft_kwargs = self.default_review_kwargs.copy()
        draft_kwargs['state'] = constants.DRAFT
        draft_review = models.Review.create_review(**draft_kwargs)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, draft_review.pk]),
            {
                'project': self.project.pk,
                'trash': True,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
            }
        )
        self.assertStatusCode(response, 302)
        draft_review.refresh_from_db()
        self.assertEqual(draft_review.state, constants.CANCELLED)

    def test_post_delete_non_draft(self):
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, self.review.pk]),
            {
                'project': self.project.pk,
                'trash': True,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
            }
        )
        self.assertStatusCode(response, 400)

    def test_delete_attachment_on_draft(self):
        self.review.state = constants.DRAFT
        self.review.save(update_fields=['state'])
        attachment = self.review.revision.attachments.all()[0]
        response = self.client.delete(reverse('delete-review-attachment', kwargs={
            'proj_slug': self.project.slug,
            'review_pk': self.review.pk,
            'attachment_pk': attachment.pk
        }))
        self.assertFalse(
            models.Attachment.objects.filter(pk=attachment.pk).exists()
        )
        self.assertStatusCode(response, 204)

    def test_delete_attachment_on_open_review(self):
        attachment = self.review.revision.attachments.all()[0]
        response = self.client.delete(reverse('delete-review-attachment', kwargs={
            'proj_slug': self.project.slug,
            'review_pk': self.review.pk,
            'attachment_pk': attachment.pk
        }))
        self.assertTrue(
            models.Attachment.objects.filter(pk=attachment.pk).exists()
        )
        self.assertStatusCode(response, 404)

    def test_post_update_review(self):
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, self.review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'delete_attachments': self.review.revision.attachments.values_list(
                    'pk', flat=True
                ),
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
                'form-0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'form-0-description': 'Test Description',
                'form-0-sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.revision.description, 'Updated Description')
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 0)
        self.assertEqual(obj.revision.attachments.count(), 1)
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'image')
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_post_update_review_reopen(self):
        title = 'Test Title Update Review POST'
        self.review.update_state(constants.CLOSED)
        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, self.review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'delete_attachments': self.review.revision.attachments.values_list(
                    'pk', flat=True
                ),
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
                'form-0-attachment': File(BytesIO(b'test_file_1'), name='test_file_1.png'),
                'form-0-description': 'Test Description',
                'form-0-sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.description, 'Test Description')
        self.assertEqual(obj.revision.description, 'Updated Description')
        self.assertEqual(obj.case_link, 'http://www.example.org/1/')
        self.assertEqual(obj.reviewer_set.active().count(), 3)
        self.assertEqual(obj.follower_set.active().count(), 0)
        self.assertEqual(obj.revision.attachments.count(), 1)
        attachment = obj.revision.attachments.get()
        self.assertEqual(attachment.attachment_type, 'image')
        self.assertEqual(attachment.description, 'Test Description')
        self.assertEqual(attachment.sort_order, 1)
        self.assertEqual(obj.reviewrevision_set.count(), 2)
        self.assertEqual(len(mail.outbox), 6)
        self.assertEqual(
            models.Reminder.objects.filter(review=obj, active=True).count(),
            4
        )

    def test_post_update_review_no_attachments(self):
        ''' Attachments from the previous revision should be copied over '''
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, self.review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.revision.attachments.count(), 2)
        self.assertEqual(obj.revision.number, 2)

    def test_post_update_draft_review_with_errors(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        self.default_review_kwargs['title'] = ''
        self.default_review_kwargs['description'] = ''
        self.default_review_kwargs['reviewers'] = []
        self.default_review_kwargs['followers'] = []
        review = models.Review.create_review(**self.default_review_kwargs)
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, review.pk]),
            {
                'title': '',
                'description': '',
                'reviewers': [],
                'case_link': 'example.org',
                'project': self.project.pk,
                'state': constants.OPEN,
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
            }
        )
        self.assertStatusCode(response, 200)
        self.assertFormError(
            response, 'review_form', 'reviewers',
            'This field is required'
        )
        self.assertFormError(
            response, 'review_form', 'title',
            'This field is required'
        )
        self.assertFormError(
            response, 'review_form', 'description',
            'This field is required'
        )

    def test_post_update_review_keep_one_attachment(self):
        """ Test for asserting that a Creator can bring Attachments over from
        the previous revision into the next revision
        """
        title = 'Test Title Update Review POST'
        self.assertEqual(len(mail.outbox), 0)
        first_attachment, second_attachment = self.review.revision.attachments.all()
        response = self.client.post(
            reverse('edit-review', args=[self.project.slug, self.review.pk]),
            {
                'title': title,
                'description': 'Updated Description',
                'case_link': 'http://www.example.org/1/',
                'reviewers': self.test_users.values_list('pk', flat=True),
                'followers': [],
                'project': self.project.pk,
                'state': constants.OPEN,
                'delete_attachments': models.Attachment.objects.filter(
                    pk=first_attachment.pk
                ).values_list('pk', flat=True),
                'form-TOTAL_FORMS': 4,
                'form-INITIAL_FORMS': 0,
                'form-MIN_NUM_FORMS': 0,
                'form-MAX_NUM_FORMS': 5,
                'form-0-attachment': File(BytesIO(b'added_file'), name='added_file.png'),
                'form-0-description': 'Test Description',
                'form-0-sort_order': 1,
            }
        )
        self.assertStatusCode(response, 302)
        obj = models.Review.objects.get(title=title)
        event = obj.event_set.get(event_type__code=models.EventType.DEMO_UPDATED)
        self.assertEqual(event.related_object, obj)
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.title, title)
        self.assertEqual(obj.revision.attachments.count(), 2)
        second_attach_content = second_attachment.attachment.file.read()
        updated_attach_content = obj.revision.attachments.all()[0].attachment.file.read()
        self.assertEqual(second_attach_content, updated_attach_content)
        self.assertEqual(obj.revision.number, 2)

    def test_update_reviewer_status(self):
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        url = reverse(
            'update-reviewer-status', args=[self.project.slug, self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': constants.APPROVED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'reviewer_state_changed': False,
            'new_state': '',
            'reviewer_status': constants.APPROVED,
            'success': True,
            'errors': {},
        })
        event = reviewer.events.get(
            event_type__code=models.EventType.REVIEWER_APPROVED
        )
        self.assertEqual(event.related_object, reviewer)

    def test_update_reviewer_status_failure(self):
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        url = reverse(
            'update-reviewer-status', args=[self.project.slug, self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': 'BOGUS',
        })
        self.assertStatusCode(response, 400)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'reviewer_state_changed': False,
            'new_state': '',
            'reviewer_status': reviewer.status,
            'success': False,
            'errors': {
                'status': ['Select a valid choice. BOGUS is not one of the available choices.'],
            },
        })

    def test_update_reviewer_status_state_change(self):
        self.assertEqual(len(mail.outbox), 0)
        self.review.reviewer_set.update(status=constants.APPROVED)
        user = User.objects.get(username='test_user_0')
        self.client.logout()
        self.client.login(username=user.username, password='testing')
        reviewer = models.Reviewer.objects.get(
            review=self.review,
            reviewer=user,
        )
        reviewer.status = constants.REVIEWING
        reviewer.save(update_fields=['status'])
        reviewer = models.Reviewer.objects.get(pk=reviewer.pk)
        self.assertEqual(self.review.reviewer_state, constants.REVIEWING)
        self.assertEqual(reviewer.status, constants.REVIEWING)
        url = reverse('update-reviewer-status', kwargs={
            'proj_slug': self.project.slug,
            'review_pk': self.review.pk,
            'reviewer_pk': reviewer.pk
        })
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': constants.APPROVED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'reviewer_state_changed': True,
            'new_state': constants.APPROVED,
            'reviewer_status': constants.APPROVED,
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
            'update-reviewer-status', args=[self.project.slug, self.review.pk, reviewer.pk]
        )
        response = self.client.post(url, {
            'review': self.review.pk,
            'reviewer': reviewer.pk,
            'status': 'BOGUS',
        })
        self.assertStatusCode(response, 404)

    def test_update_review_state_draft_to_open(self):
        draft_kwargs = self.default_review_kwargs
        draft_kwargs['state'] = constants.DRAFT
        draft_kwargs['title'] = 'Draft Open'
        draft_review = models.Review.create_review(**draft_kwargs)
        orig_created = draft_review.created
        url = reverse('update-review-state', args=[self.project.slug, draft_review.pk])
        response = self.client.post(url, {
            'review': draft_review.pk,
            'state': constants.OPEN
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.OPEN,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        draft_review.refresh_from_db()
        self.assertEqual(draft_review.state, constants.OPEN)
        self.assertEqual(len(mail.outbox), 5)
        event = self.review.event_set.get(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertEqual(event.related_object, self.review)
        self.assertNotEqual(orig_created, draft_review.created)

    def test_update_review_state_draft_to_open_no_reviewers(self):
        draft_kwargs = self.default_review_kwargs
        draft_kwargs['state'] = constants.DRAFT
        draft_kwargs['reviewers'] = []
        draft_review = models.Review.create_review(**draft_kwargs)
        url = reverse('update-review-state', args=[self.project.slug, draft_review.pk])
        response = self.client.post(url, {
            'review': draft_review.pk,
            'state': constants.OPEN
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.DRAFT,
            'state_changed': False,
            'success': False,
            'errors': {'review': ['Demo must have Reviewers to be published.']},
        })
        draft_review.refresh_from_db()
        self.assertEqual(draft_review.state, constants.DRAFT)

    def test_update_review_state_draft_to_open_no_description(self):
        draft_kwargs = self.default_review_kwargs
        draft_kwargs['state'] = constants.DRAFT
        draft_kwargs['description'] = ''
        draft_review = models.Review.create_review(**draft_kwargs)
        url = reverse('update-review-state', args=[self.project.slug, draft_review.pk])
        response = self.client.post(url, {
            'review': draft_review.pk,
            'state': constants.OPEN
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.DRAFT,
            'state_changed': False,
            'success': False,
            'errors': {'review': ['Demo must contain a description to be published.']},
        })
        draft_review.refresh_from_db()
        self.assertEqual(draft_review.state, constants.DRAFT)

    def test_update_review_state_draft_to_open_no_title(self):
        draft_kwargs = self.default_review_kwargs
        draft_kwargs['state'] = constants.DRAFT
        draft_kwargs['title'] = ''
        draft_review = models.Review.create_review(**draft_kwargs)
        url = reverse('update-review-state', args=[self.project.slug, draft_review.pk])
        response = self.client.post(url, {
            'review': draft_review.pk,
            'state': constants.OPEN
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.DRAFT,
            'state_changed': False,
            'success': False,
            'errors': {'review': ['Demo must have a title to be published.']},
        })
        draft_review.refresh_from_db()
        self.assertEqual(draft_review.state, constants.DRAFT)

    def test_update_review_state_paused(self):
        self.assertEqual(len(mail.outbox), 0)
        url = reverse('update-review-state', args=[self.project.slug, self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': constants.PAUSED
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.PAUSED,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        self.assertEqual(len(mail.outbox), 5)
        event = self.review.event_set.get(
            event_type__code=models.EventType.DEMO_PAUSED
        )
        self.assertEqual(event.related_object, self.review)

    def test_update_review_state_closed(self):
        self.assertEqual(len(mail.outbox), 0)
        self.review.last_action_by = self.co_owner
        self.review.save(update_fields=['last_action_by'])
        url = reverse('update-review-state', args=[self.project.slug, self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': constants.CLOSED
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.CLOSED,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        self.review.refresh_from_db()
        self.assertEqual(len(mail.outbox), 5)
        event = self.review.event_set.get(
            event_type__code=models.EventType.DEMO_CLOSED
        )
        self.assertEqual(event.related_object, self.review)
        # last_action_by reset
        self.assertEqual(self.review.last_action_by, self.user)

    def test_update_review_state_aborted(self):
        url = reverse('update-review-state', args=[self.project.slug, self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': constants.ABORTED
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.ABORTED,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        event = self.review.event_set.get(
            event_type__code=models.EventType.DEMO_ABORTED
        )
        self.assertEqual(event.related_object, self.review)

    def test_update_review_state_reopened(self):
        self.review.state = constants.CLOSED
        self.review.save(update_fields=['state'])
        url = reverse('update-review-state', args=[self.project.slug, self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': constants.OPEN,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': constants.OPEN,
            'state_changed': True,
            'success': True,
            'errors': {},
        })
        self.assertEqual(len(mail.outbox), 5)
        event = self.review.event_set.get(
            event_type__code=models.EventType.DEMO_OPENED
        )
        self.assertEqual(event.related_object, self.review)

    def test_update_review_state_invalid(self):
        self.client.logout()
        self.client.login(username='test_user_0', password='testing')
        url = reverse('update-review-state', args=[self.project.slug, self.review.pk])
        response = self.client.post(url, {
            'review': self.review.pk,
            'state': constants.OPEN,
        })
        self.assertStatusCode(response, 400)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'state': self.review.state,
            'state_changed': False,
            'success': False,
            'errors': {
                'review': ['Select a valid choice. '
                           'That choice is not one of the available choices.']
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
        self.assertEqual(obj.creator_set.active().get().user, self.user)

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
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertIn(test_user, obj.reviewers.all())

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'reviewer': self.user.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_follower(self):
        follower = User.objects.get(username='follower_0')
        response = self.client.get(reverse('review-list'), {
            'follower': follower.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertIn(follower, obj.followers.all())

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'reviewer': self.user.pk
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_state(self):
        response = self.client.get(reverse('review-list'), {
            'state': constants.OPEN,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, constants.OPEN)

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'state': constants.CLOSED,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)
        self.assertIn('form', response.context)

    def test_review_list_filter_by_reviewer_state(self):
        response = self.client.get(reverse('review-list'), {
            'reviewer_state': constants.REVIEWING,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, constants.OPEN)

        # Let's show that filtering works the other way too
        response = self.client.get(reverse('review-list'), {
            'reviewer_state': constants.APPROVED,
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

    def test_review_list_search_no_drafts(self):
        self.review.state = constants.DRAFT
        self.review.save()
        response = self.client.get(reverse('review-list'), {
            'title': self.review.title
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_review_list_no_cancellations(self):
        self.review.state = constants.CANCELLED
        self.review.save()
        response = self.client.get(reverse('review-list'), {
            'title': self.review.title
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_revew_list_search_error(self):
        response = self.client.get(reverse('review-list'), {
            'state': 'notastate'
        })
        self.assertStatusCode(response, 200)
        self.assertFormError(
            response, 'form', 'state',
            'Select a valid choice. notastate is not one of the available choices.'
        )

    def test_review_list_all_the_filters(self):
        test_user = User.objects.get(username='test_user_0')
        response = self.client.get(reverse('review-list'), {
            'reviewer': test_user.pk,
            'creator': self.user.pk,
            'state': constants.OPEN,
            'reviewer_state': constants.REVIEWING,
            'title': 'test',
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertIn('form', response.context)
        obj = response.context['object_list'][0]
        self.assertEqual(obj.state, constants.OPEN)
        self.assertEqual(obj.creator_set.active().get().user, self.user)
        self.assertEqual(obj.reviewer_state, constants.REVIEWING)
        self.assertIn(test_user, obj.reviewers.all())
        self.assertEqual(obj.title, 'Test Title')

    def test_review_json_no_match(self):
        response = self.client.post(
            reverse('reviews-search-json', args=[self.project.slug]),
            {'title': 'zxy'}
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'count': 0,
            'reviews': []
        })

    def test_review_json_by_pk(self):
        response = self.client.post(
            reverse('reviews-search-json', args=[self.project.slug]),
            {'pk': self.review.pk}
        )
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
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
        for follower in self.review.follower_set.all():
            self.assertIn(
                {
                    'user_pk': follower.user.pk, 'name': follower.user.userprofile.name,
                    'follower_pk': follower.pk, 'review_pk': follower.review.pk,
                    'created': follower.created.isoformat(),
                    'modified': follower.modified.isoformat(),
                    'user_profile_url': follower.user.userprofile.get_absolute_url(),
                },
                followers
            )
        for reviewer in self.review.reviewer_set.all():
            self.assertIn(
                {
                    'user_pk': reviewer.reviewer.pk,
                    'reviewer_pk': reviewer.pk,
                    'name': reviewer.reviewer.userprofile.name,
                    'reviewer_status': constants.REVIEWING,
                    'review_pk': reviewer.review.pk,
                    'is_active': reviewer.is_active,
                    'last_viewed': None,
                    'created': reviewer.created.isoformat(),
                    'modified': reviewer.modified.isoformat(),
                    'user_profile_url': reviewer.reviewer.userprofile.get_absolute_url(),
                },
                reviewers
            )

    def test_review_json_all_the_filters(self):
        test_user = User.objects.get(username='test_user_0')
        response = self.client.post(
            reverse('reviews-search-json', args=[self.project.slug]),
            {
                'reviewer': test_user.pk,
                'creator': self.user.pk,
                'state': constants.OPEN,
                'reviewer_state': constants.REVIEWING,
                'title': 'test',
            }
        )
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        review_obj = models.Review.objects.get(pk=review['pk'])
        self.assertEqual(review['title'], 'Test Title')
        self.assertEqual(review['creators'][0]['name'], self.user.userprofile.name)
        self.assertEqual(review['state'], constants.OPEN)
        self.assertEqual(review['reviewer_state'], constants.REVIEWING)
        self.assertEqual(review['url'], review_obj.get_absolute_url())
        reviewers = review['reviewers']
        self.assertIn(test_user.pk, [x['user_pk'] for x in reviewers])

    def test_review_json_without_project_slug(self):
        project = models.Project.objects.create(
            name='Second Project', slug='second-project', description=''
        )
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Test Title 2'
        second_review_kwargs['project'] = project
        second_review = models.Review.create_review(**second_review_kwargs)
        response = self.client.post(reverse('reviews-search-json'), {
            'title': 'test'
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        self.assertEqual(review['title'], 'Test Title')
        self.assertEqual(review['pk'], self.review.pk)
        self.assertNotEqual(review['pk'], second_review.pk)

    def test_review_json_posting_project_pk(self):
        project = models.Project.objects.create(
            name='Second Project', slug='second-project', description=''
        )
        models.ProjectMember.objects.create(
            project=project, user=self.user
        )
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Test Title 2'
        second_review_kwargs['project'] = project
        second_review = models.Review.create_review(**second_review_kwargs)
        response = self.client.post(reverse('reviews-search-json'), {
            'title': 'test',
            'project_pk': self.project.pk,
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        self.assertEqual(review['title'], 'Test Title')
        self.assertEqual(review['pk'], self.review.pk)
        self.assertNotEqual(review['pk'], second_review.pk)

    def test_review_json_posting_project_pk_unauthorized(self):
        project = models.Project.objects.create(
            name='Second Project', slug='second-project', description=''
        )
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Test Title 2'
        second_review_kwargs['project'] = project
        models.Review.create_review(**second_review_kwargs)
        response = self.client.post(reverse('reviews-search-json'), {
            'title': 'test',
            'project_pk': project.pk,
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 0)

    def test_review_search_description(self):
        response = self.client.post(reverse('reviews-search-json'), {
            'title': 'Description'
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        self.assertEqual(review['pk'], self.review.pk)

    def test_review_search_revision_description(self):
        revision = self.review.revision
        revision.description = 'zebra'
        revision.save(update_fields=['description'])
        response = self.client.post(reverse('reviews-search-json'), {
            'title': 'Zebra'
        })
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(json_data['count'], 1)
        review = json_data['reviews'][0]
        self.assertEqual(review['pk'], self.review.pk)

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
            reverse('review-detail', kwargs={
                'proj_slug': self.project.slug,
                'pk': review.pk
            }),
            status_code=301,
        )

    def test_review_redirect_view_not_found(self):
        self.assertFalse(models.Review.objects.filter(pk=10000).exists())
        response = self.client.get(
            reverse('dt-redirect', kwargs={'pk': 10000})
        )
        self.assertStatusCode(response, 404)

    def test_review_detail_json_get(self):
        response = self.client.get(
            reverse(
                'review-json',
                kwargs={'proj_slug': self.project.slug, 'pk': self.review.pk}
            )
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, self.review.to_json())

    def test_review_detail_quick_edit(self):
        url = reverse(
            'review-json',
            kwargs={'proj_slug': self.project.slug, 'pk': self.review.pk}
        )
        self.review.last_action_by = self.co_owner
        self.review.save()
        self.review.reviewer_state = constants.APPROVED
        response = self.client.post(url, {
            'title': 'test_review_detail_quick_edit',
            'description': 'test review detail quick edit',
            'case_link': 'http://example.org/quick-edit',
            'state': constants.CLOSED,
            'is_public': True
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))['review']
        self.review.refresh_from_db()
        self.assertEqual(data['title'], 'test_review_detail_quick_edit')
        self.assertEqual(self.review.title, 'test_review_detail_quick_edit')
        self.assertEqual(data['description'], 'test review detail quick edit')
        self.assertEqual(self.review.description, 'test review detail quick edit')
        self.assertEqual(data['case_link'], 'http://example.org/quick-edit')
        self.assertEqual(self.review.case_link, 'http://example.org/quick-edit')
        self.assertEqual(data['state'], constants.CLOSED)
        self.assertEqual(self.review.state, constants.CLOSED)
        self.assertTrue(data['is_public'])
        self.assertTrue(self.review.is_public)
        self.assertEqual(self.review.last_action_by, self.user)

    def test_review_detail_quick_edit_errors(self):
        url = reverse(
            'review-json',
            kwargs={'proj_slug': self.project.slug, 'pk': self.review.pk}
        )
        self.review.reviewer_state = constants.APPROVED
        response = self.client.post(url, {
            'state': 'Not a real state',
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            data['errors'],
            {'state': ['Select a valid choice. '
                       'Not a real state is not one of the available choices.']}
        )

    def test_review_detail_quick_edit_forbidden(self):
        ''' Quick Edit of a Demo is only available to the Creator '''
        url = reverse(
            'review-json',
            kwargs={'proj_slug': self.project.slug, 'pk': self.review.pk}
        )
        self.client.logout()
        assert self.client.login(
            username='test_user_1',
            password='testing'
        )
        response = self.client.post(url, {
            'state': constants.CLOSED
        })
        self.assertStatusCode(response, 403)
        self.assertEqual(
            json.loads(response.content.decode('utf-8'))['errors'],
            ['Only the owners of a Demo can edit it'],
        )
