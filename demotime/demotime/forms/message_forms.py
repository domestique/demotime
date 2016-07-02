from django import forms

from demotime import models


class BulkMessageUpdateForm(forms.Form):

    READ = 'read'
    UNREAD = 'unread'
    DELETED = 'delete'
    UNDELETED = 'undelete'

    messages = forms.ModelMultipleChoiceField(
        queryset=models.MessageBundle.objects.none(),
        required=False,
    )
    action = forms.ChoiceField(choices=(
        (READ, READ.capitalize()),
        (UNREAD, UNREAD.capitalize()),
        (DELETED, DELETED.capitalize()),
        (UNDELETED, UNDELETED.capitalize()),
    ))
    mark_all_read = forms.BooleanField(required=False)

    def __init__(self, user, *args, **kwargs):
        super(BulkMessageUpdateForm, self).__init__(*args, **kwargs)
        self.fields['messages'].queryset = models.MessageBundle.objects.filter(
            owner=user
        )

