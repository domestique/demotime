import json

from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from demotime import constants, models


class CanViewMixin(UserPassesTestMixin):

    require_admin_privileges = False
    require_superuser_privileges = False
    raise_exception = True

    def test_func(self):
        if self.request.user.is_authenticated() and self.request.user.is_superuser:
            return True

        if self.require_superuser_privileges:
            if not self.request.user.is_authenticated():
                self.raise_exception = False
            return False

        if (getattr(self, 'review', None)
                and self.review.state == constants.DRAFT
                and self.request.user != self.review.creator):
            return False

        if (not self.require_admin_privileges) and (
                self.project.is_public or (self.review and self.review.is_public)
        ):
            # Public Project/Review, so they're in
            return True

        if not self.request.user.is_authenticated():
            # Otherwise we're going to need to see some authentication
            self.raise_exception = False
            return False

        user_list = User.objects.filter(
            Q(projectmember__project=self.project) |
            Q(groupmember__group__project=self.project)
        ).distinct()

        if user_list.filter(pk=self.request.user.pk).exists():
            # User is in an applicable group or is a direct member of a project,
            # but we need to check admin privileges first, if applicable
            if self.require_admin_privileges:
                admin_groups = self.request.user.groupmember_set.filter(
                    group__projectgroup__project=self.project,
                    group__projectgroup__is_admin=True
                )
                admin_user = self.request.user.projectmember_set.filter(
                    project=self.project,
                    is_admin=True
                )
                if admin_user.exists() or admin_groups.exists():
                    # User is either in an admin group associated with this
                    # project or is a direct ProjectMember with admin rights
                    return True
                else:
                    return False
            else:
                # Don't care about admin privileges, just care that they are in
                # a proper group or a direct member
                return True

        # If everything else was skipped, let's go ahead and send them packing.
        return False


class JsonView(View):

    content_type = 'application/json'
    status = None

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


class CanViewJsonView(CanViewMixin, JsonView):
    pass


class IndexView(TemplateView):
    template_name = 'demotime/index.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['open_demos'] = models.Review.objects.filter(
            creator=self.request.user,
            state=constants.OPEN,
        )
        context['drafts'] = models.Review.objects.filter(
            creator=self.request.user,
            state=constants.DRAFT
        )

        open_review_pks = models.Reviewer.objects.filter(
            reviewer=self.request.user,
            review__state=constants.OPEN
        ).values_list('review__pk', flat=True)

        context['open_reviews'] = models.Review.objects.filter(
            pk__in=open_review_pks
        )

        approved_review_pks = models.Reviewer.objects.filter(
            reviewer=self.request.user,
            review__state=constants.OPEN,
            status=constants.REVIEWING
        ).values_list('review__pk', flat=True)
        context['approved_reviews'] = models.Review.objects.filter(
            pk__in=approved_review_pks
        )

        context['followed_demos'] = models.Review.objects.filter(
            followers=self.request.user,
            state=constants.OPEN,
        )

        updated_demos = models.UserReviewStatus.objects.filter(
            user=self.request.user,
        ).order_by('-modified')[:5]
        context['updated_demos'] = updated_demos

        message_bundles = models.MessageBundle.objects.filter(
            owner=self.request.user,
            read=False,
            deleted=False,
        ).order_by('-modified')[:5]
        context['message_bundles'] = message_bundles
        return context


index_view = IndexView.as_view()
