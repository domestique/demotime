from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect

from demotime import constants, forms, models
from demotime.views import CanViewMixin


class ProjectDashboard(CanViewMixin, DetailView):
    template_name = 'demotime/project_dashboard.html'
    model = models.Project
    slug_url_kwarg = 'proj_slug'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.review = None
        return super(ProjectDashboard, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectDashboard, self).get_context_data(**kwargs)
        context['open_demos'] = models.Review.objects.filter(
            project=self.project,
            state=constants.OPEN,
        )[:5]
        user_updated_demos = models.UserReviewStatus.objects.filter(
            review__project=self.project,
            user=self.request.user,
        ).order_by('-modified')[:5]
        context['user_updated_demos'] = user_updated_demos
        context['updated_demos'] = models.Review.objects.filter(
            project=self.project
        ).order_by('-modified')[:5]
        context['is_admin'] = self.request.user.is_admin(self.project)
        return context


class ProjectDetail(CanViewMixin, DetailView):
    template_name = 'demotime/project_detail.html'
    model = models.Project
    slug_url_kwarg = 'proj_slug'
    require_admin_privileges = True

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.review = None
        return super(ProjectDetail, self).dispatch(request, *args, **kwargs)


class ProjectAdmin(CanViewMixin, DetailView):
    template_name = 'demotime/project_admin.html'
    model = models.Project
    slug_url_kwarg = 'proj_slug'
    require_admin_privileges = True

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.review = None
        self.member_formset = modelformset_factory(
            models.ProjectMember,
            form=forms.ProjectMemberForm,
            max_num=User.objects.count(),
            extra=User.objects.count(),
        )
        self.edit_member_formset = modelformset_factory(
            models.ProjectMember, form=forms.EditProjectMemberForm,
            max_num=0, extra=0
        )
        self.group_formset = modelformset_factory(
            models.ProjectGroup,
            form=forms.ProjectGroupForm,
            max_num=models.Group.objects.count(),
            extra=models.Group.objects.count()
        )
        self.edit_group_formset = modelformset_factory(
            models.ProjectGroup,
            form=forms.EditProjectGroupForm,
            max_num=0,
            extra=0,
        )
        return super(ProjectAdmin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectAdmin, self).get_context_data(**kwargs)
        context['project_form'] = forms.ProjectForm(instance=self.project)
        context['member_formset'] = self.member_formset(
            queryset=models.ProjectMember.objects.none(),
            prefix='add_member',
        )
        context['edit_member_formset'] = self.edit_member_formset(
            queryset=models.ProjectMember.objects.filter(project=self.project),
            prefix='edit_member'
        )
        context['group_formset'] = self.group_formset(
            queryset=models.ProjectGroup.objects.none(),
            prefix='add_group',
        )
        context['edit_group_formset'] = self.edit_group_formset(
            queryset=models.ProjectGroup.objects.filter(project=self.project),
            prefix='edit_group'
        )
        return context

    def post(self, request, *args, **kwargs):
        project_form = forms.ProjectForm(instance=self.project, data=request.POST)
        member_fs = self.member_formset(
            queryset=models.ProjectMember.objects.none(),
            data=request.POST,
            prefix='add_member',
        )
        edit_member_fs = self.edit_member_formset(
            queryset=models.ProjectMember.objects.filter(project=self.project),
            data=request.POST,
            prefix='edit_member',
        )
        group_fs = self.group_formset(
            queryset=models.ProjectGroup.objects.none(),
            data=request.POST,
            prefix='add_group',
        )
        edit_group_fs = self.edit_group_formset(
            queryset=models.ProjectGroup.objects.filter(project=self.project),
            data=request.POST,
            prefix='edit_group',
        )
        project_form_valid = project_form.is_valid()
        member_fs_valid = member_fs.is_valid()
        edit_member_fs_valid = edit_member_fs.is_valid()
        group_fs_valid = group_fs.is_valid()
        edit_group_fs_valid = edit_group_fs.is_valid()
        forms_valid = all(
            x for x in (
                project_form_valid, member_fs_valid, edit_member_fs_valid,
                group_fs_valid, edit_group_fs_valid
            )
        )
        if forms_valid:
            # Project Form
            project_form.save()

            # New Members
            members = member_fs.save(commit=False)
            for member in members:
                member.project = self.project
                member.save()

            # Edited Members
            edited_data = edit_member_fs.cleaned_data
            for member_data in edited_data:
                if not member_data:
                    continue

                member = models.ProjectMember.objects.get(
                    project=self.project,
                    user=member_data['user'],
                )
                member.is_admin = member_data['is_admin']
                if member_data['delete']:
                    member.delete()
                else:
                    member.save()

            # New Groups
            groups = group_fs.save(commit=False)
            for group in groups:
                group.project = self.project
                group.save()

            edited_group_data = edit_group_fs.cleaned_data
            for group_data in edited_group_data:
                if not group_data:
                    continue

                group = models.ProjectGroup.objects.get(
                    project=self.project,
                    group=group_data['group'],
                )
                group.is_admin = group_data['is_admin']
                if group_data['delete']:
                    group.delete()
                else:
                    group.save()

        return redirect('project-detail', proj_slug=self.project.slug)

project_dashboard = ProjectDashboard.as_view()
project_detail = ProjectDetail.as_view()
project_admin = ProjectAdmin.as_view()
