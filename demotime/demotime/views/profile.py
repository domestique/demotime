from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models


class EditProfileView(DetailView):

    model = models.UserProfile
    template_name = 'demotime/edit_profile.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.profile_form = None
        self.lookup_kwargs = kwargs
        return super(EditProfileView, self).dispatch(request, *args, **kwargs)

    def init_profile_form(self, data=None, files=None):
        profile = self.request.user.userprofile
        kwargs = {
            'instance': profile,
            'initial': {
                'email': self.request.user.email,
                'bio': profile.bio,
                'display_name': profile.display_name,
            },
        }
        if data:
            kwargs['data'] = data
        if files:
            kwargs['files'] = files
        return forms.UserProfileForm(**kwargs)

    def get_object(self, *args, **kwargs):
        lookup_dict = {'user': self.request.user}
        if self.lookup_kwargs.get('pk'):
            lookup_dict['pk'] = self.lookup_kwargs['pk']
        if self.lookup_kwargs.get('username'):
            lookup_dict['user__username'] = self.lookup_kwargs['username']

        return get_object_or_404(
            models.UserProfile,
            **lookup_dict
        )

    def get_context_data(self, *args, **kwargs):
        context = super(EditProfileView, self).get_context_data(*args, **kwargs)
        if not self.profile_form:
            self.profile_form = self.init_profile_form()

        context['profile_form'] = self.profile_form
        return context

    def post(self, request, *args, **kwargs):
        self.profile_form = self.init_profile_form(data=request.POST, files=request.FILES)
        if self.profile_form.is_valid() and request.user == self.get_object().user:
            profile = self.request.user.userprofile
            user = profile.user
            data = self.profile_form.cleaned_data
            if data.get('avatar'):
                # If they didn't upload anything, we'll keep what we have,
                # otherwise we set it
                profile.avatar = data['avatar']
            if data.get('password_one'):
                user.set_password(data.get('password_one'))

            user.email = data.get('email')
            profile.bio = data.get('bio')
            profile.display_name = data.get('display_name')
            profile.save()
            user.save()
            return redirect('profile', pk=profile.pk)
        else:
            return self.get(request, *args, **kwargs)


class ProfileView(DetailView):

    model = models.UserProfile
    template_name = 'demotime/profile.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.profile_form = None
        self.lookup_args = kwargs
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        lookup_dict = {}
        if self.lookup_args.get('pk'):
            lookup_dict['pk'] = self.lookup_args['pk']
        if self.lookup_args.get('username'):
            lookup_dict['user__username'] = self.lookup_args['username']

        return get_object_or_404(
            models.UserProfile,
            **lookup_dict
        )

    def get_context_data(self, *args, **kwargs):
        context = super(ProfileView, self).get_context_data(*args, **kwargs)
        obj = self.get_object()
        context['open_demos'] = models.Review.objects.filter(
            creator__user=obj.user,
            creator__active=True,
            state=models.reviews.OPEN,
        )
        context['open_reviews'] = models.Review.objects.filter(
            reviewers=obj.user,
            state=models.reviews.OPEN
        )
        context['followed_demos'] = models.Review.objects.filter(
            followers=obj.user,
            state=models.reviews.OPEN,
        )
        owner_viewing = self.request.user == obj.user
        context['owner_viewing'] = owner_viewing
        return context


profile_view = ProfileView.as_view()
edit_profile_view = EditProfileView.as_view()
