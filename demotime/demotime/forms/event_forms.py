from django import forms

from demotime import models


class EventFilterForm(forms.Form):

    event_type = forms.ModelMultipleChoiceField(
        queryset=models.EventType.objects.all(),
        to_field_name='code',
        required=False
    )
    review = forms.ModelChoiceField(
        queryset=models.Review.objects.none(),
        required=False
    )
    exclude_type = forms.ModelMultipleChoiceField(
        queryset=models.EventType.objects.all(),
        to_field_name='code',
        required=False
    )

    def __init__(self, project, *args, **kwargs):
        super(EventFilterForm, self).__init__(*args, **kwargs)
        self.fields['review'].queryset = models.Review.objects.filter(
            project=project
        )
