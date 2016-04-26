import json

from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from demotime import models


class CanViewMixin(UserPassesTestMixin):

    def test_func(self):
        if not self.request.user.is_authenticated():
            return False

        if not self.project:
            return True

        if self.project.is_public or (self.review and self.review.is_public):
            return True

        user_list = User.objects.filter(
            Q(projectmember__project=self.project) |
            Q(groupmember__group__project=self.project)
        ).distinct()

        if user_list.filter(pk=self.request.user.pk).exists():
            return True

        return False


class JsonView(CanViewMixin, View):

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

        context['followed_demos'] = models.Review.objects.filter(
            followers=self.request.user,
            state=models.reviews.OPEN,
        )

        updated_demos = models.UserReviewStatus.objects.filter(
            user=self.request.user,
        ).order_by('-modified')[:5]
        context['updated_demos'] = updated_demos

        message_bundles = models.MessageBundle.objects.filter(
            owner=self.request.user,
            deleted=False,
        ).order_by('-modified')[:5]
        context['message_bundles'] = message_bundles
        return context


index_view = IndexView.as_view()
