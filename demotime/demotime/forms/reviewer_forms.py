from django import forms

from demotime import models


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
