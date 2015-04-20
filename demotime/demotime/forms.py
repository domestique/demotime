from django import forms
from django.contrib.auth.models import User

from demotime import models


class ReviewForm(forms.ModelForm):

    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5})
    )

    def __init__(self, user, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['reviewers'].queryset = User.objects.exclude(
            pk=user.pk).exclude(username='demotime_sys')

        for key, value in self.fields.iteritems():
            self.fields[key].widget.attrs['class'] = 'form-control'

    class Meta:
        model = models.Review
        fields = (
            'reviewers', 'description', 'title',
            'case_link',
        )


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
        queryset=models.Message.objects.none()
    )
    action = forms.ChoiceField(choices=(
        (READ, READ.capitalize()),
        (UNREAD, UNREAD.capitalize()),
        (DELETED, DELETED.capitalize()),
        (UNDELETED, UNDELETED.capitalize()),
    ))

    def __init__(self, user, *args, **kwargs):
        super(BulkMessageUpdateForm, self).__init__(*args, **kwargs)
        self.fields['messages'].queryset = models.Message.objects.filter(
            receipient=user
        )
