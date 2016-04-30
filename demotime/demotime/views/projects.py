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
        return super(ProjectAdmin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectAdmin, self).get_context_data(**kwargs)
        context['project_form'] = forms.ProjectForm(instance=self.project)
        return context

    def post(self, request, *args, **kwargs):
        form = forms.ProjectForm(instance=self.project, data=request.POST)
        if form.is_valid():
            pass # data = form.cleaned_data

        return redirect('project-detail', proj_slug=self.project.slug)

project_dashboard = ProjectDashboard.as_view()
project_detail = ProjectDetail.as_view()
project_admin = ProjectAdmin.as_view()
