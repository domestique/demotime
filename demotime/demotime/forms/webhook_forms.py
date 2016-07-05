from django import forms

from demotime import models


class WebHookForm(forms.ModelForm):

    delete = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(WebHookForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            del self.fields['delete']

    class Meta:
        model = models.WebHook
        fields = (
            'trigger_event', 'target'
        )
