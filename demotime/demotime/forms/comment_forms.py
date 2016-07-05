from django import forms

from demotime import models


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

        for key, value in self.fields.items():
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


class UpdateCommentForm(CommentForm, AttachmentForm):

    def __init__(self, *args, **kwargs):
        super(UpdateCommentForm, self).__init__(*args, **kwargs)
        self.fields['attachment_type'].required = False

    def clean_attachment_type(self):
        data = self.cleaned_data
        if data.get('attachment') and not data.get('attachment_type'):
            raise forms.ValidationError('Attachments require an Attachment Type')

        return data['attachment_type']
