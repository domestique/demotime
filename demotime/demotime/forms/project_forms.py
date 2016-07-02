from django import forms
from django.contrib.auth.models import User

from demotime import models


class ProjectMemberForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        if project:
            self.base_fields['user'].queryset = User.objects.filter(
                userprofile__user_type=models.UserProfile.USER,
            ).exclude(
                projectmember__project=project
            ).order_by('username')

        return super(ProjectMemberForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.ProjectMember
        fields = (
            'user', 'is_admin'
        )


class EditProjectMemberForm(forms.ModelForm):

    delete = forms.BooleanField(required=False)

    class Meta:
        model = models.ProjectMember
        fields = (
            'user', 'is_admin'
        )


class ProjectGroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        if project:
            self.base_fields['group'].queryset = models.Group.objects.exclude(
                projectgroup__project=project
            ).order_by('name')

        return super(ProjectGroupForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.ProjectGroup
        fields = (
            'group', 'is_admin'
        )


class EditProjectGroupForm(forms.ModelForm):

    delete = forms.BooleanField(required=False)

    class Meta:
        model = models.ProjectGroup
        fields = (
            'group', 'is_admin'
        )


class ProjectForm(forms.ModelForm):

    class Meta:
        model = models.Project
        fields = (
            'name', 'slug', 'description', 'is_public',
        )
