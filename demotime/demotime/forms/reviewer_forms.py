from django import forms

from demotime import constants, models


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
            creator__user=user,
            creator__active=True,
            pk=review_pk
        )

    def clean(self):
        cleaned_data = super(ReviewStateForm, self).clean()
        state = cleaned_data.get('state')
        review = cleaned_data.get('review')
        if review and review.state == constants.DRAFT and state == constants.OPEN:
            if not review.reviewer_set.active().exists():
                self.add_error(
                    'review', 'Demo must have Reviewers to be published.'
                )
            if not review.revision.description:
                self.add_error(
                    'review', 'Demo must contain a description to be published.'
                )

            if not review.title:
                self.add_error(
                    'review', 'Demo must have a title to be published.'
                )

        return cleaned_data
