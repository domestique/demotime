from django.contrib.auth.models import User
from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect

from demotime import constants, forms, models
from demotime.views import CanViewMixin


class GroupListView(CanViewMixin, ListView):

    model = models.Group
    template = 'demotime/group_list.html'
    require_superuser_privileges = True
    project = None


class GroupEditView(CanViewMixin, TemplateView):

    template_name = 'demotime/group_manage.html'
    require_superuser_privileges = True
    project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('group_slug'):
            self.group = get_object_or_404(
                models.Group, slug=kwargs['group_slug']
            )
            self.form = forms.GroupForm(instance=self.group)
        else:
            self.form = forms.GroupForm()
            self.group = None

        return super(GroupEditView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupEditView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['group'] = self.group

        return context

    def post(self, request, *args, **kwargs):
        self.form = forms.GroupForm(instance=self.group, data=request.POST)
        if self.form.is_valid():
            group = self.form.save(commit=False)
            group.save()
            members = self.form.cleaned_data['members']
            models.GroupMember.objects.filter(
                group=group
            ).exclude(
                user__in=members
            ).delete()
            for user in members:
                models.GroupMember.create_group_member(
                    user=user, group=group
                )
            return redirect('group-list')

        return self.get(request, *args, **kwargs)

group_list = GroupListView.as_view()
manage_group = GroupEditView.as_view()
