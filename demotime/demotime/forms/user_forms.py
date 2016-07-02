from django import forms

from demotime import models


class UserProfileForm(forms.ModelForm):

    email = forms.EmailField()
    password_one = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_two = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        data = super(UserProfileForm, self).clean()
        password_one = data.get('password_one')
        password_two = data.get('password_two')
        if password_one or password_two:
            if password_one != password_two:
                raise forms.ValidationError('Passwords do not match')

        return data

    class Meta:
        model = models.UserProfile
        fields = ('display_name', 'bio', 'avatar')
