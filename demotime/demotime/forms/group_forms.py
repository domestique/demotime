from django import forms

from demotime import models


class GroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['members'].queryset = models.UserProxy.objects.filter(
            userprofile__user_type=models.UserProfile.USER
        )

    class Meta:
        model = models.Group
        fields = (
            'name', 'slug', 'description', 'members'
        )


class GroupMemberForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GroupMemberForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['user'].queryset = models.UserProxy.objects.filter(
            userprofile__user_type=models.UserProfile.USER
        )
        self.fields['group'].widget = forms.HiddenInput()

    class Meta:
        model = models.GroupMember
        fields = (
            'user', 'group', 'is_admin',
        )


class GroupTypeForm(forms.ModelForm):

    class Meta:
        model = models.GroupType
        fields = (
            'name', 'slug'
        )
