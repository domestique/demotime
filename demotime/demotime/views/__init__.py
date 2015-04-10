from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import models


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
