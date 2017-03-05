from django import forms

from demotime import constants, models


class AttachmentForm(forms.Form):

    OBJECT_TYPES = (
        ('review', 'Review'),
        ('comment', 'Comment')
    )

    object_type = forms.ChoiceField(choices=OBJECT_TYPES)
    object_pk = forms.IntegerField()

    def clean(self):
        super(AttachmentForm, self).clean()
        if self.errors:
            # We already know we're busted, let's move on
            return

        data = self.cleaned_data
        if data['object_type'] == constants.REVIEW:
            model = models.Review
        elif data['object_type'] == constants.COMMENT:
            model = models.Comment

        try:
            obj = model.objects.get(pk=data['object_pk'])
        except model.DoesNotExist:
            obj = None
            raise forms.ValidationError('Invalid object provided for attachment')
        else:
            if data['object_type'] == constants.REVIEW:
                obj = obj.revision # Grab latest revision and return that

        self.cleaned_data['object'] = obj
