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
    object_pk = forms.IntegerField()
    reaction_type = forms.ChoiceField(choices=[])
    review = forms.ModelChoiceField(queryset=models.Review.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reaction_types = models.ReactionType.objects.values_list(
            'code', flat=True
        )
        reaction_choices = [(code, code) for code in reaction_types]
        self.fields['reaction_type'].choices = reaction_choices

    def clean(self):
        super().clean()
        data = self.cleaned_data
        object_type = data.get('object_type')
        if object_type == 'attachment':
            model = models.Attachment
        elif object_type == 'comment':
            model = models.Comment
        elif object_type == 'event':
            model = models.Event
        else:
            model = models.ReviewRevision

        try:
            data['reaction_object'] = model.objects.get(pk=data['object_pk'])
        except model.DoesNotExist:
            self.add_error('object_pk', 'Invalid PK supplied')
        return data


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
