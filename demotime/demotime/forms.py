from django import forms
from django.contrib.auth.models import User

from demotime import models


class ReviewForm(forms.ModelForm):

    def __init__(self, user, project, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.project = project
        self.fields['reviewers'].queryset = self.project.members
        self.fields['followers'].queryset = self.project.members
        self.fields['followers'].required = False

        for key, value in self.fields.iteritems():
            self.fields[key].widget.attrs['class'] = 'form-control'

        if self.instance.pk:
            self.fields['description'].required = False

    class Meta:
        model = models.Review
        fields = (
            'reviewers', 'description', 'title',
            'case_link', 'followers',
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
        queryset=User.objects.exclude(
            userprofile__user_type=models.UserProfile.SYSTEM
        ).order_by('username')
    )
    reviewer = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.exclude(
            userprofile__user_type=models.UserProfile.SYSTEM
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
        for key, value in self.fields.iteritems():
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


class CommentForm(forms.ModelForm):

    thread = forms.ModelChoiceField(
        queryset=models.CommentThread.objects.none(),
        widget=forms.widgets.HiddenInput(),
        required=False
    )

    def __init__(self, thread=None, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        if thread:
            self.fields['thread'].queryset = models.CommentThread.objects.filter(
                pk=thread.pk
            )
            self.fields['thread'].required = True

        for key, value in self.fields.iteritems():
            self.fields[key].widget.attrs['class'] = 'form-control'

    class Meta:
        model = models.Comment
        fields = (
            'comment',
        )


class AttachmentForm(forms.Form):

    attachment = forms.FileField(
        required=False,
        widget=forms.widgets.FileInput(
            attrs={'class': 'form-control'}
        )
    )
    attachment_type = forms.ChoiceField(
        choices=models.Attachment.ATTACHMENT_TYPE_CHOICES,
        widget=forms.Select
    )
    description = forms.CharField(
        required=False,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control'}),
        max_length=2048
    )


class ReviewerStatusForm(forms.Form):

    status = forms.ChoiceField(choices=models.Reviewer.STATUS_CHOICES)
    review = forms.ModelChoiceField(
        queryset=models.Review.objects.none,
        widget=forms.widgets.HiddenInput
    )
    reviewer = forms.ModelChoiceField(
        queryset=models.Reviewer.objects.none,
        widget=forms.widgets.HiddenInput
    )

    def __init__(self, reviewer, *args, **kwargs):
        super(ReviewerStatusForm, self).__init__(*args, **kwargs)
        self.fields['review'].queryset = models.Review.objects.filter(
            pk=reviewer.review.pk)
        self.fields['reviewer'].queryset = models.Reviewer.objects.filter(
            pk=reviewer.pk)


class ReviewStateForm(forms.Form):

    state = forms.ChoiceField(choices=models.Review.STATUS_CHOICES)
    review = forms.ModelChoiceField(
        queryset=models.Review.objects.none()
    )

    def __init__(self, user, review_pk, *args, **kwargs):
        super(ReviewStateForm, self).__init__(*args, **kwargs)
        self.fields['review'].queryset = models.Review.objects.filter(
            creator=user,
            pk=review_pk
        )


class UserProfileForm(forms.ModelForm):

    email = forms.EmailField()
    password_one = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_two = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        data = super(UserProfileForm, self).clean()
        password_one = data.get('password_one')
        password_two = data.get('password_two')
        if password_one or password_two:
            if password_one != password_two:
                raise forms.ValidationError('Passwords do not match')

        return data

    class Meta:
        model = models.UserProfile
        fields = ('display_name', 'bio', 'avatar')


class BulkMessageUpdateForm(forms.Form):

    READ = 'read'
    UNREAD = 'unread'
    DELETED = 'delete'
    UNDELETED = 'undelete'

    messages = forms.ModelMultipleChoiceField(
        queryset=models.MessageBundle.objects.none()
    )
    action = forms.ChoiceField(choices=(
        (READ, READ.capitalize()),
        (UNREAD, UNREAD.capitalize()),
        (DELETED, DELETED.capitalize()),
        (UNDELETED, UNDELETED.capitalize()),
    ))

    def __init__(self, user, *args, **kwargs):
        super(BulkMessageUpdateForm, self).__init__(*args, **kwargs)
        self.fields['messages'].queryset = models.MessageBundle.objects.filter(
            owner=user
        )


class UpdateCommentForm(CommentForm, AttachmentForm):

    def __init__(self, *args, **kwargs):
        super(UpdateCommentForm, self).__init__(*args, **kwargs)
        self.fields['attachment_type'].required = False

    def clean_attachment_type(self):
        data = self.cleaned_data
        if data.get('attachment') and not data.get('attachment_type'):
            raise forms.ValidationError('Attachments require an Attachment Type')

        return data['attachment_type']


class ProjectMemberForm(forms.ModelForm):

    class Meta:
        model = models.ProjectMember
        fields = (
            'user', 'is_admin'
        )


class EditProjectMemberForm(forms.ModelForm):

    delete = forms.BooleanField(required=False)

    class Meta:
        model = models.ProjectMember
        fields = (
            'user', 'is_admin'
        )


class ProjectGroupForm(forms.ModelForm):

    class Meta:
        model = models.ProjectGroup
        fields = (
            'group', 'is_admin'
        )


class EditProjectGroupForm(forms.ModelForm):

    delete = forms.BooleanField(required=False)

    class Meta:
        model = models.ProjectGroup
        fields = (
            'group', 'is_admin'
        )


class ProjectForm(forms.ModelForm):

    class Meta:
        model = models.Project
        fields = (
            'name', 'description', 'is_public',
        )
