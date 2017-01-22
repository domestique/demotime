from django import forms
from django.contrib.auth.models import User

from demotime import models


class ReactionForm(forms.Form):

    REACTABLE_OBJECT_TYPES = (
        ('attachment', 'Attachment'),
        ('comment', 'Comment'),
        ('event', 'Event'),
        ('revision', 'Revision'),
    )

    object_type = forms.ChoiceField(choices=REACTABLE_OBJECT_TYPES)
    reaction_type = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reaction_types = models.ReactionType.objects.values_list(
            'code', flat=True
        )
        reaction_choices = [(code, code) for code in reaction_types]
        self.fields['reaction_type'].choices = reaction_choices


class ReactionFilterForm(forms.Form):

    reaction_type = forms.ModelChoiceField(
        queryset=models.ReactionType.objects.all(),
        required=False,
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
    )
    review = forms.ModelChoiceField(
        queryset=models.Review.objects.all(),
        required=False,
    )
