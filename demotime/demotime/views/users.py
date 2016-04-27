from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import models
from . import JsonView


class UserAPI(JsonView):

    status = 200
    ACTIONS = (
        'search_users', 'add_follower', 'find_follower', 'drop_follower',
        'add_reviewer', 'find_reviewer', 'drop_reviewer'
    )

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = None
        return super(UserAPI, self).dispatch(*args, **kwargs)

    @property
    def default_user_list(self):
        sys_user = User.objects.get(username='demotime_sys')
        return User.objects.exclude(
            pk=sys_user.pk
        )

    def _build_json(self, users, errors, success=True):
        json_dict = {
            'errors': errors,
            'users': [],
            'success': success
        }
        for user in users:
            json_dict['users'].append({
                'name': user.userprofile.name,
                'pk': user.pk
            })

        return json_dict

    def _filter_users_by_name(self, users, name):
        return users.filter(
            Q(username__icontains=name) |
            Q(userprofile__display_name__icontains=name)
        )

    def _search_users(self, post_data):
        name = post_data.get('name')
        users = self._filter_users_by_name(
            self.default_user_list.exclude(pk=self.request.user.pk),
            name
        )
        return self._build_json(users, {})

    def _add_follower(self, post_data):
        if 'user_pk' not in post_data:
            self.status = 400
            return {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['user_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }

        follower = models.Follower.objects.filter(
            review=self.review,
            user=user
        )
        is_reviewer = models.Reviewer.objects.filter(
            review=self.review,
            reviewer=user
        ).exists()
        if follower.exists() or is_reviewer or self.review.creator == user:
            self.status = 400
            return {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        else:
            notify_follower = self.request.user != user
            notify_creator = self.request.user != self.review.creator
            follower = models.Follower.create_follower(
                review=self.review,
                user=user,
                notify_follower=notify_follower,
                notify_creator=notify_creator
            )
            return {
                'follower_name': follower.user.userprofile.name,
                'follower_user_pk': follower.user.pk,
                'success': True,
                'errors': {},
            }

    def _find_follower(self, post_data):
        if not self.review:
            self.status = 400
            return self._build_json(
                users=[],
                errors={'review': 'Find follower requires a Review PK'},
                success=False
            )

        users = self.default_user_list.exclude(
            follower__review=self.review,
        ).exclude(
            reviewer__review=self.review,
        ).exclude(
            pk=self.review.creator.pk,
        )
        if post_data.get('name'):
            users = self._filter_users_by_name(users, post_data['name'])
        return self._build_json(users, {})

    def _drop_follower(self, post_data):
        post_data = self.request.POST.copy()
        if 'user_pk' not in post_data:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['user_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }

        if self.request.user != self.review.creator and self.request.user != user:
            self.status = 403
            return {
                'success': False,
                'errors': {
                    'user_pk': "Not allowed to remove others from a demo you don't own"
                }
            }

        try:
            follower = models.Follower.objects.get(
                review=self.review,
                user=user
            )
        except models.Follower.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not currently on review'}
            }
        else:
            follower.delete()
            return {
                'success': True,
                'errors': {},
            }

    def _add_reviewer(self, post_data):
        if 'user_pk' not in post_data:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['user_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }

        reviewer = models.Reviewer.objects.filter(
            review=self.review,
            reviewer=user
        )
        if reviewer.exists() or self.review.creator == user:
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        else:
            count, _ = models.Follower.objects.filter(
                review=self.review,
                user=user,
            ).delete()
            notify_reviewer = self.request.user != user
            notify_creator = self.request.user != self.review.creator
            reviewer = models.Reviewer.create_reviewer(
                review=self.review,
                reviewer=user,
                notify_reviewer=notify_reviewer,
                notify_creator=notify_creator
            )
            return {
                'reviewer_name': reviewer.reviewer.userprofile.name,
                'reviewer_user_pk': reviewer.reviewer.pk,
                'reviewer_status': reviewer.status,
                'removed_follower': count > 0,
                'success': True,
                'errors': {},
            }

    def _find_reviewer(self, post_data):
        if not self.review:
            self.status = 400
            return self._build_json(
                users=[],
                errors={'review': 'Find reviewer requires a Review PK'},
                success=False
            )

        users = self.default_user_list.exclude(
            reviewer__review=self.review
        ).exclude(pk=self.review.creator.pk)
        if post_data.get('name'):
            users = self._filter_users_by_name(users, post_data['name'])
        return self._build_json(users, {})

    def _drop_reviewer(self, post_data):
        post_data = self.request.POST.copy()
        if 'user_pk' not in post_data:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }

        if self.request.user != self.review.creator:
            self.status = 400
            return {
                'success': False,
                'errors': {
                    'user_pk': "Can not remove reviewers from reviews you don't own"
                }
            }

        try:
            user = User.objects.get(pk=post_data['user_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not found'}
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
                'errors': {'user_pk': 'User not currently on review'}
            }
        else:
            reviewer._send_reviewer_message(deleted=True)
            reviewer.delete()
            return {
                'success': True,
                'errors': {},
            }

    def post(self, *args, **kwargs):
        post_data = self.request.POST.copy()
        action = post_data.get('action')
        if 'review_pk' in post_data:
            self.review = get_object_or_404(models.Review, pk=post_data['review_pk'])
        if action in self.ACTIONS:
            return getattr(self, '_{}'.format(action))(post_data)

        self.status = 400
        return {
            'errors': {'action': 'Invalid Action'},
            'users': [],
            'success': False
        }

user_api = UserAPI.as_view()
