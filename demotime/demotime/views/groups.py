from django.forms import modelformset_factory
from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect

from demotime import forms, models
from demotime.views import CanViewMixin


class GroupListView(CanViewMixin, ListView):

    model = models.Group
    template = 'demotime/group_list.html'
    require_superuser_privileges = True
    project = None

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)
        context['group_types'] = models.GroupType.objects.all()

        return context


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


class GroupMemberManageView(CanViewMixin, TemplateView):

    template_name = 'demotime/group_member_manage.html'
    require_superuser_privileges = True
    project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(
            models.Group, slug=kwargs['group_slug']
        )

        self.member_formset = modelformset_factory(
            models.GroupMember,
            form=forms.GroupMemberForm,
            max_num=models.GroupMember.objects.filter(group=self.group).count(),
            extra=0,
        )

        return super(GroupMemberManageView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupMemberManageView, self).get_context_data(**kwargs)
        context['group'] = self.group
        context['member_formset'] = self.member_formset(
            queryset=models.GroupMember.objects.filter(group=self.group),
        )

        return context

    def post(self, request, *args, **kwargs):
        member_form = self.member_formset(
            queryset=models.GroupMember.objects.filter(group=self.group),
            data=request.POST,
        )
        if member_form.is_valid():
            for gm_data in member_form.cleaned_data:
                gm = models.GroupMember.objects.get(
                    group=gm_data['group'],
                    user=gm_data['user']
                )
                gm.is_admin = gm_data['is_admin']
                gm.save(update_fields=['is_admin'])

            return redirect('group-list')

        return self.get(request, *args, **kwargs)


class GroupTypeManageView(CanViewMixin, TemplateView):

    template_name = 'demotime/group_type_manage.html'
    require_superuser_privileges = True
    project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('slug'):
            self.group_type = get_object_or_404(
                models.GroupType,
                slug=kwargs['slug']
            )
        else:
            self.group_type = None

        self.form = forms.GroupTypeForm(instance=self.group_type)
        return super(GroupTypeManageView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupTypeManageView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['group_type'] = self.group_type

        return context

    def post(self, request, *args, **kwargs):
        self.form = forms.GroupTypeForm(
            data=request.POST, instance=self.group_type
        )
        if self.form.is_valid():
            self.form.save()
            return redirect('group-list')

        return self.get(request, *args, **kwargs)


group_list = GroupListView.as_view()
manage_group = GroupEditView.as_view()
manage_group_admins = GroupMemberManageView.as_view()
manage_group_type = GroupTypeManageView.as_view()
