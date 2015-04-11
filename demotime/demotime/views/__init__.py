import json

from django.http import HttpResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import models


class JsonView(View):

    content_type = 'application/json'
    status = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        response = super(JsonView, self).dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            return response
        else:
            return self.render_to_response(response)

    def render_to_response(self, context):
        content = json.dumps(context)
        return HttpResponse(
            content,
            content_type=self.content_type,
            status=self.status,
        )


class IndexView(TemplateView):
    template_name = 'demotime/index.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['open_demos'] = models.Review.objects.filter(
            creator=self.request.user,
            state=models.reviews.OPEN,
        )
        context['open_reviews'] = models.Review.objects.filter(
            reviewers=self.request.user,
            state=models.reviews.OPEN,
        )
        # TODO: Figure out how to show the recently updated ones
        context['updated_demos'] = []
        return context

index_view = IndexView.as_view()
