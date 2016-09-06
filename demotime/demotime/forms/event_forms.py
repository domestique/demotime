from django import forms
from django.contrib.auth.models import User

from demotime import models


class EventFilterForm(forms.Form):

    event_type = forms.ModelChoiceField(
        queryset=models.EventType.objects.all(),
        to_field_name='code',
        required=False
    )
    review = forms.ModelChoiceField(
        queryset=models.Review.objects.none(),
        required=False
    )

    def __init__(self, project, *args, **kwargs):
        super(EventFilterForm, self).__init__(*args, **kwargs)
        self.fields['review'].queryset = models.Review.objects.filter(
            project=project
        )
