from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect

from demotime import forms, models
from demotime.views import CanViewMixin


class WebHooksManageView(CanViewMixin, TemplateView):
    template_name = 'demotime/webhook.html'
    require_admin_privileges = True

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=kwargs.get('proj_slug')
        )
        if kwargs.get('hook_pk'):
            self.hook = get_object_or_404(
                models.WebHook,
                pk=kwargs.get('hook_pk')
            )
        else:
            self.hook = models.WebHook(project=self.project)

        self.form = forms.WebHookForm(instance=self.hook)
        return super(WebHooksManageView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WebHooksManageView, self).get_context_data(**kwargs)
        context.update({
            'form': self.form,
            'hook': self.hook,
            'project': self.project,
        })
        return context

    @property
    def redirect_url(self):

        return reverse('project-detail', args=[self.project.slug])

    def post(self, request, *args, **kwargs):
        self.form = forms.WebHookForm(instance=self.hook, data=request.POST)
        if self.form.is_valid():
            data = self.form.cleaned_data
            if data.get('delete'):
                self.hook.delete()
                return redirect(self.redirect_url)

            if self.hook.pk:
                self.hook.target = data.get('target')
                self.hook.trigger_event = data.get('trigger_event')
                self.hook.save(
                    update_fields=['modified', 'target', 'trigger_event']
                )
            else:
                models.WebHook.create_webhook(
                    self.project,
                    data.get('target'),
                    data.get('trigger_event')
                )

            return redirect(self.redirect_url)

        return super(WebHooksManageView, self).get(request, *args, **kwargs)


manage_hooks = WebHooksManageView.as_view()
