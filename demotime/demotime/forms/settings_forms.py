from django import forms

from demotime import models


class ProjectSettingForm(forms.ModelForm):

    raw_value = forms.CharField(label='Setting Value', widget=forms.TextInput)

    def clean_raw_value(self):
        raw_value = self.cleaned_data['raw_value']
        try:
            self.instance.raw_value = raw_value
            self.instance.value
        except:
            raise forms.ValidationError(
                'Invalid value provided for Setting Type {}'.format(
                    self.instance.get_setting_type_display()
                )
            )
        else:
            return raw_value

    class Meta:
        fields = ('raw_value', )
        model = models.Setting
