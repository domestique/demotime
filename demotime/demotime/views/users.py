from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import constants, models
from demotime.views import JsonView


class FollowerAPIMixin(object):

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
            user=user,
            is_active=True,
        )
        is_reviewer = models.Reviewer.objects.filter(
            review=self.review,
            reviewer=user,
            is_active=True,
        ).exists()
        if follower.exists() or is_reviewer or self.review.creator_set.active().filter(user=user).exists():
            self.status = 400
            return {
                'follower_name': '',
                'follower_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        else:
            follower = models.Follower.create_follower(
                review=self.review,
                user=user,
                creator=self.request.user,
                draft=self.review.state == constants.DRAFT,
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

        reviewers = self.review.reviewer_set.active().values_list(
            'reviewer__pk', flat=True
        )
        followers = self.review.follower_set.active().values_list(
            'user__pk', flat=True
        )
        creators = self.review.creator_set.active().values_list(
            'user__pk', flat=True
        )
        excluded_pks =  tuple(reviewers) + tuple(creators) + tuple(followers)
        users = self.default_user_list.exclude(
            pk__in=excluded_pks
        ).filter(
            Q(projectmember__project=self.review.project) |
            Q(groupmember__group__project=self.review.project)
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

        if (not self.review.creator_set.active().filter(user=self.request.user).exists() and
                self.request.user != user):
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
                user=user,
                is_active=True
            )
        except models.Follower.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not currently on review'}
            }
        else:
            follower.drop_follower(
                self.request.user,
                draft=self.review.state == constants.DRAFT,
            )
            return {
                'success': True,
                'errors': {},
            }


class ReviewerAPIMixin(object):

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
            reviewer=user,
            is_active=True
        )
        if reviewer.exists() or self.review.creator_set.active().filter(user=user).exists():
            self.status = 400
            return {
                'reviewer_name': '',
                'reviewer_user_pk': '',
                'reviewer_status': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        else:
            count = models.Follower.objects.filter(
                review=self.review,
                user=user,
            ).update(is_active=False)
            reviewer = models.Reviewer.create_reviewer(
                review=self.review,
                reviewer=user,
                creator=self.request.user,
                draft=self.review.state == constants.DRAFT,
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

        reviewers = self.review.reviewer_set.active().values_list(
            'reviewer__pk', flat=True
        )
        creators = self.review.creator_set.active().values_list(
            'user__pk', flat=True
        )
        excluded_pks =  tuple(reviewers) + tuple(creators)
        users = self.default_user_list.exclude(
            pk__in=excluded_pks
        ).filter(
            Q(projectmember__project=self.review.project) |
            Q(groupmember__group__project=self.review.project)
        )
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
                reviewer=user,
                is_active=True
            )
        except models.Reviewer.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not currently on review'}
            }

        if (
                not self.review.creator_set.active().filter(user=self.request.user).exists() and
                self.request.user != reviewer.reviewer
            ):
            self.status = 400
            return {
                'success': False,
                'errors': {
                    'user_pk': "Can not remove reviewers from reviews you don't own"
                }
            }

        reviewer.drop_reviewer(
            self.request.user,
            draft=self.review.state == constants.DRAFT
        )
        return {
            'success': True,
            'errors': {},
        }


class CreatorAPIMixin(object):

    def _add_creator(self, post_data):
        if 'user_pk' not in post_data:
            self.status = 400
            return {
                'creator_name': '',
                'creator_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User identifier missing'}
            }

        try:
            user = User.objects.get(pk=post_data['user_pk'])
        except User.DoesNotExist:
            self.status = 400
            return {
                'creator_name': '',
                'creator_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User not found'}
            }

        reviewer = models.Reviewer.objects.filter(
            review=self.review,
            reviewer=user,
            is_active=True
        )
        creator = models.Creator.objects.filter(
            user=user,
            review=self.review,
            active=True
        )
        if creator.exists() or self.review.creator_set.active().filter(user=user).exists():
            self.status = 400
            return {
                'creator_name': '',
                'creator_user_pk': '',
                'success': False,
                'errors': {'user_pk': 'User already on review'}
            }
        else:
            follower_count = models.Follower.objects.filter(
                review=self.review,
                user=user,
            ).update(is_active=False)
            reviewer_count = models.Reviewer.objects.filter(
                review=self.review,
                reviewer=user,
            ).update(is_active=False)
            creator = models.Creator.create_creator(
                user, self.review, notify=True, adding_user=self.request.user
            )
            return {
                'creator_name': creator.user.userprofile.name,
                'creator_user_pk': creator.user.pk,
                'removed_follower': follower_count > 0,
                'removed_reviewer': reviewer_count > 0,
                'success': True,
                'errors': {},
            }

    def _find_creator(self, post_data):
        if not self.review:
            self.status = 400
            return self._build_json(
                users=[],
                errors={'review': 'Find creator requires a Review PK'},
                success=False
            )

        excluded_pks = self.review.creator_set.active().values_list(
            'user__pk', flat=True
        )
        users = self.default_user_list.exclude(
            pk__in=excluded_pks
        ).filter(
            Q(projectmember__project=self.review.project) |
            Q(groupmember__group__project=self.review.project)
        )
        if post_data.get('name'):
            users = self._filter_users_by_name(users, post_data['name'])
        return self._build_json(users, {})

    def _drop_creator(self, post_data):
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

        try:
            creator = models.Creator.objects.get(
                review=self.review,
                user=user,
                active=True
            )
        except models.Reviewer.DoesNotExist:
            self.status = 400
            return {
                'success': False,
                'errors': {'user_pk': 'User not currently on review'}
            }

        if (
                not self.review.creator_set.active().filter(user=self.request.user).exists() and
                self.request.user != creator.user
            ):
            self.status = 400
            return {
                'success': False,
                'errors': {
                    'user_pk': "Can not remove creators from reviews you don't own"
                }
            }

        creator.drop_creator(self.request.user)
        return {
            'success': True,
            'errors': {},
        }


class UserAPI(JsonView, FollowerAPIMixin, CreatorAPIMixin, ReviewerAPIMixin):

    status = 200
    ACTIONS = (
        'search_users', 'add_follower', 'find_follower', 'drop_follower',
        'add_reviewer', 'find_reviewer', 'drop_reviewer',
        'add_creator', 'find_creator', 'drop_creator',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None

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

    # pylint: disable=no-self-use
    def _build_json(self, users, errors, success=True):
        json_dict = {
            'errors': errors,
            'users': [],
            'success': success
        }
        for user in users:
            json_dict['users'].append({
                'name': user.userprofile.name,
                'username': user.username,
                'pk': user.pk,
                'url': user.userprofile.get_absolute_url(),
            })

        return json_dict

    # pylint: disable=no-self-use
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

    # pylint: disable=unused-argument
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
