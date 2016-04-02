from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import models
from . import JsonView


class ReviewerFinder(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = None
        if 'pk' in kwargs:
            self.review = get_object_or_404(models.Review, pk=kwargs.get('pk'))
        return super(ReviewerFinder, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        post_data = self.request.POST.copy()
        if 'reviewer_name' not in post_data:
            self.status = 400
            return {
                'reviewers': [],
                'success': False,
                'errors': {'reviewer_name': 'Reviewer Name missing'}
            }

        name = post_data.get('reviewer_name')
        if self.review:
            existing_reviewers = self.review.reviewer_set.values_list(
                'reviewer', flat=True
            )
            eligible_reviewers = User.objects.exclude(
                pk__in=existing_reviewers
            ).exclude(
                pk=self.review.creator.pk
            )
        else:
            sys_user = User.objects.get(username='demotime_sys')
            eligible_reviewers = User.objects.exclude(
                pk__in=(self.request.user.pk, sys_user.pk)
            )

        reviewers = eligible_reviewers.filter(
            Q(username__icontains=name) |
            Q(userprofile__display_name__icontains=name)
        )
        json_data = {'reviewers': [], 'success': True, 'errors': {}}
        for reviewer in reviewers:
            json_data['reviewers'].append({
                'name': reviewer.userprofile.__unicode__(),
                'pk': reviewer.pk,
            })
        return json_data


class AddReviewer(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = get_object_or_404(models.Review, pk=kwargs.get('pk'))
        return super(AddReviewer, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        post_data = self.request.POST.copy()
        if 'reviewer_pk' not in post_data:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'Reviewer identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['reviewer_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'User not found'}
            }

        reviewer = models.Reviewer.objects.filter(
            review=self.review,
            reviewer=user
        )
        if reviewer.exists() or self.review.creator == user:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'reviewer_pk': 'User already on review'}
            }
        else:
            reviewer = models.Reviewer.create_reviewer(
                self.review, user, non_revision=True
            )
            return {
                'reviewer_name': reviewer.reviewer.userprofile.__unicode__(),
                'reviewer_status': reviewer.status,
                'success': True,
                'errors': {},
            }


class DeleteReviewer(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = get_object_or_404(
            models.Review,
            pk=kwargs.get('pk'),
            creator=self.request.user,
        )
        return super(DeleteReviewer, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        post_data = self.request.POST.copy()
        if 'reviewer_pk' not in post_data:
            self.status = 400
            return {
                'success': False,
                'errors': {'reviewer_pk': 'Reviewer identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['reviewer_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'reviewer_pk': 'User not found'}
            }

        try:
            reviewer = models.Reviewer.objects.get(
                review=self.review,
                reviewer=user
            )
        except models.Reviewer.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'reviewer_pk': 'User not currently on review'}
            }
        else:
            reviewer._send_reviewer_message(deleted=True)
            reviewer.delete()
            return {
                'success': True,
                'errors': {},
            }
reviewer_finder = ReviewerFinder.as_view()
add_reviewer = AddReviewer.as_view()
delete_reviewer = DeleteReviewer.as_view()
