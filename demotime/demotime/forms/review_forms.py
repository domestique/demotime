from django import forms
from django.contrib.auth.models import User

from demotime import models


class ReviewQuickEditForm(forms.Form):

    state = forms.ChoiceField(
        choices=models.Review.STATUS_CHOICES,
        required=False
    )
    title = forms.CharField(required=False)
    description = forms.CharField(required=False)
    case_link = forms.CharField(required=False)
    is_public = forms.BooleanField(required=False)


class ReviewForm(forms.ModelForm):

    def __init__(self, user, project, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.project = project
        user_queryset = self.project.project_members.exclude(pk=user.pk)
        self.fields['reviewers'].queryset = user_queryset
        self.fields['followers'].queryset = user_queryset
        self.fields['followers'].required = False

        for key, value in self.fields.items():
            self.fields[key].widget.attrs['class'] = 'form-control'

        if self.instance.pk:
            self.fields['description'].required = False

    class Meta:
        model = models.Review
        fields = (
            'reviewers', 'description', 'title',
            'case_link', 'followers', 'is_public'
        )


class ReviewFilterForm(forms.Form):

    STATE_CHOICES = (
        ('', '-----------'),
    ) + models.Review.STATUS_CHOICES

    REVIEWER_STATE_CHOICES = (
        ('', '-----------'),
    ) + models.Review.REVIEWER_STATE_CHOICES

    SORT_OPTIONS = (
        ('', '-----------'),
        ('newest', 'Newest'),
        ('oldest', 'Oldest'),
    )

    title = forms.CharField(required=False)
    state = forms.ChoiceField(
        required=False,
        choices=STATE_CHOICES,
    )
    reviewer_state = forms.ChoiceField(
        required=False,
        choices=REVIEWER_STATE_CHOICES,
    )
    creator = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(
            userprofile__user_type=models.UserProfile.USER
        ).order_by('username')
    )
    reviewer = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(
            userprofile__user_type=models.UserProfile.USER
        ).order_by('username')
    )
    follower = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(
            userprofile__user_type=models.UserProfile.USER
        ).order_by('username')
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_OPTIONS,
    )
    pk = forms.IntegerField(
        label='',
        required=False,
        widget=forms.HiddenInput
    )

    def __init__(self, projects, *args, **kwargs):
        super(ReviewFilterForm, self).__init__(*args, **kwargs)
        self.projects = projects
        for key, value in self.fields.items():
            self.fields[key].widget.attrs['class'] = 'form-control'

    def get_reviews(self, initial_qs=None):
        ''' Retrieve all the reviews matching the critiera. Should be called
        after is_valid()
        '''
        if self.errors:
            return models.Review.objects.none()

        qs = models.Review.objects.all() if not initial_qs else initial_qs
        qs = qs.filter(project__in=self.projects)
        data = self.cleaned_data
        if data.get('reviewer'):
            qs = qs.filter(reviewer__reviewer=data['reviewer'])

        if data.get('follower'):
            qs = qs.filter(follower__user=data['follower'])

        if data.get('creator'):
            qs = qs.filter(creator=data['creator'])

        if data.get('state'):
            qs = qs.filter(state=data['state'])

        if data.get('reviewer_state'):
            qs = qs.filter(reviewer_state=data['reviewer_state'])

        if data.get('title'):
            qs = qs.filter(title__icontains=data['title'])

        if data.get('sort_by'):
            sorting = data['sort_by']
            if sorting == 'newest':
                qs = qs.order_by('-modified')
            elif sorting == 'oldest':
                qs = qs.order_by('modified')

        if data.get('pk'):
            qs = qs.filter(pk=data['pk'])

        return qs.distinct()
