from django.shortcuts import get_object_or_404, redirect
from django.forms import formset_factory
from django.views.generic import (
    TemplateView, DetailView, ListView, RedirectView, View
)
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest

from demotime import constants, forms, models
from demotime.views import CanViewMixin, CanViewJsonView, JsonView


class ReviewDetail(CanViewMixin, DetailView):
    template_name = 'demotime/review.html'
    model = models.Review

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.review = None
        self.revision = None
        self.user = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        if self.kwargs.get('rev_num'):
            try:
                self.revision = models.ReviewRevision.objects.get(
                    number=self.kwargs['rev_num'],
                    review__pk=self.kwargs['pk']
                )
            except models.ReviewRevision.DoesNotExist:
                review = get_object_or_404(
                    models.Review,
                    pk=kwargs['pk'],
                )
                return redirect(
                    'review-rev-detail',
                    proj_slug=self.project.slug,
                    pk=review.pk,
                    rev_num=review.revision.number,
                )
        else:
            self.revision = self.get_object().revision

        self.review = self.revision.review
        if self.request.user.is_authenticated:
            self.user = self.request.user
        return super(ReviewDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
        try:
            reviewer = models.Reviewer.objects.get(
                review=self.revision.review,
                reviewer=self.user,
                is_active=True
            )
        except models.Reviewer.DoesNotExist:
            reviewer = None
        else:
            context['reviewer_status_form'] = forms.ReviewerStatusForm(
                reviewer, initial={
                    'reviewer': reviewer,
                    'review': reviewer.review
                }
            )
            reviewer.viewed_review()

        if reviewer:
            context['reviewer'] = reviewer

        try:
            follower = models.Follower.objects.get(
                review=self.revision.review,
                user=self.user,
                is_active=True,
            )
        except models.Follower.DoesNotExist:
            follower = None
        context['follower_obj'] = follower

        try:
            creator = models.Creator.objects.get(
                review=self.revision.review,
                user=self.user,
                active=True
            )
        except models.Creator.DoesNotExist:
            creator = None
        context['creator_obj'] = creator

        if creator:
            context['review_state_form'] = forms.ReviewStateForm(
                self.request.user,
                self.revision.review.pk,
                initial={'review': self.revision.review}
            )

        models.UserReviewStatus.objects.filter(
            review=self.revision.review,
            user=self.user,
        ).update(read=True)
        context['project'] = self.project
        context['revision'] = self.revision
        context['comment_form'] = forms.CommentForm()
        context['attachment_form'] = forms.DemoAttachmentForm(prefix='0')
        return context


class CreateReviewView(View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=kwargs['proj_slug']
        )
        return super(CreateReviewView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        review = models.Review.create_review(
            creators=[request.user],
            title='',
            description='',
            case_link='',
            reviewers=[],
            followers=[],
            project=self.project,
            state=constants.DRAFT,
            attachments=[],
        )
        return redirect('edit-review', proj_slug=self.project.slug, pk=review.pk)

class EditReviewView(TemplateView):
    template_name = 'demotime/create_review.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.review = None
        self.review_inst = None
        self.comment_form = None
        self.review_form = None
        self.attachment_forms = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=kwargs['proj_slug']
        )
        self.review_inst = get_object_or_404(models.Review, pk=kwargs['pk'])
        self.project = self.review_inst.project
        self.template_name = 'demotime/edit_review.html'
        return super(EditReviewView, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk=None, *args, **kwargs):
        self.review_form = forms.ReviewForm(
            user=self.request.user,
            instance=self.review_inst,
            project=self.project,
            data=request.POST
        )
        # pylint: disable=invalid-name
        AttachmentFormSet = formset_factory(
            forms.DemoAttachmentForm, extra=10, max_num=25
        )
        self.attachment_forms = AttachmentFormSet(
            data=request.POST,
            files=request.FILES
        )
        if self.review_form.is_valid() and self.attachment_forms.is_valid():
            data = self.review_form.cleaned_data
            trash = data.pop('trash', None)
            if trash:
                if self.review_inst and self.review_inst.state == constants.DRAFT:
                    # Draft deleted!
                    self.review_inst.update_state(constants.CANCELLED)
                    return redirect('index')
                else:
                    return HttpResponseBadRequest(
                        'You can not delete a Demo that has been opened'
                    )

            co_owner = data.get('creators')
            co_owners = [request.user]
            if co_owner:
                co_owners.append(co_owner)
            data['creators'] = co_owners
            data['project'] = self.project
            data['attachments'] = []
            for form in self.attachment_forms.forms:
                if form.cleaned_data:
                    if not form.cleaned_data['attachment']:
                        continue
                    data['attachments'].append({
                        'attachment': form.cleaned_data['attachment'],
                        'description': form.cleaned_data['description'],
                        'sort_order': form.cleaned_data['sort_order'],
                    })

            review = models.Review.update_review(self.review_inst.pk, **data)

            return redirect(
                'review-rev-detail',
                proj_slug=review.project.slug,
                pk=review.pk,
                rev_num=review.revision.number
            )
        return self.get(request, *args, **kwargs)

    def get(self, request, pk=None, *args, **kwargs):
        if request.method == 'GET':
            # If we're using this method as the POST error path, let's
            # preserve the existing forms. Also, maybe this is dumb?
            description = ''
            self.review_inst = get_object_or_404(models.Review, pk=pk)
            self.template_name = 'demotime/edit_review.html'
            if self.review_inst.state == constants.DRAFT:
                description = self.review_inst.description
            self.review_form = forms.ReviewForm(
                user=self.request.user,
                instance=self.review_inst,
                project=self.project,
                initial={'description': description},
            )
            # pylint: disable=invalid-name
            AttachmentFormSet = formset_factory(
                forms.DemoAttachmentForm, extra=10, max_num=25
            )
            initial_data = [
                {'sort_order': x} for x in range(1, AttachmentFormSet.extra + 1)
            ]
            self.attachment_forms = AttachmentFormSet(initial=initial_data)
        return super(EditReviewView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditReviewView, self).get_context_data(**kwargs)
        context.update({
            'project': self.project,
            'review_form': self.review_form,
            'review_inst': self.review_inst,
            'attachment_forms': self.attachment_forms
        })
        return context


class ReviewListView(ListView):

    template_name = 'demotime/demo_list.html'
    paginate_by = 15
    model = models.Review

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ReviewListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = super(ReviewListView, self).get_queryset()
        form = forms.ReviewFilterForm(
            self.request.user.projects,
            data=self.request.GET
        )
        if form.is_valid():
            return form.get_reviews(qs)

        return models.Review.objects.none()

    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        initial = self.request.GET.copy()
        initial['state'] = initial.get('state', models.reviews.OPEN)
        context.update({
            'form': forms.ReviewFilterForm(
                self.request.user.projects,
                initial=initial,
                data=self.request.GET
            )
        })
        return context


class ReviewerStatusView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None
        self.reviewer = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        reviewer_pk = kwargs['reviewer_pk']
        self.reviewer = get_object_or_404(
            models.Reviewer, pk=reviewer_pk, reviewer=self.request.user
        )
        self.review = self.reviewer.review
        self.project = self.review.project
        return super(ReviewerStatusView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        form = forms.ReviewerStatusForm(self.reviewer, data=self.request.POST)
        if form.is_valid():
            state_changed, new_state = self.reviewer.set_status(
                form.cleaned_data['status']
            )
            return {
                'reviewer_state_changed': state_changed,
                'new_state': new_state,
                'reviewer_status': form.cleaned_data['status'],
                'success': True,
                'errors': {},
            }
        else:
            self.status = 400
            return {
                'reviewer_state_changed': False,
                'new_state': '',
                'reviewer_status': self.reviewer.status,
                'success': False,
                'errors': form.errors,
            }


class ReviewStateView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        review_pk = kwargs['pk']
        self.review = get_object_or_404(models.Review, pk=review_pk)
        self.project = self.review.project
        return super(ReviewStateView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs): # pylint: disable=unused-argument
        form = forms.ReviewStateForm(
            self.request.user, self.review.pk, data=self.request.POST
        )
        if form.is_valid():
            changed = self.review.update_state(form.cleaned_data['state'])
            if changed:
                self.review.last_action_by = self.request.user
                self.review.save(update_fields=['last_action_by'])
            return {
                'state': self.review.state,
                'state_changed': changed,
                'success': True,
                'errors': {},
            }
        else:
            self.status = 400
            return {
                'state': self.review.state,
                'state_changed': False,
                'success': False,
                'errors': form.errors,
            }


class ReviewJsonView(CanViewJsonView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = get_object_or_404(
            models.Review,
            pk=kwargs.get('pk'),
            project__slug=kwargs.get('proj_slug'),
        )
        self.project = self.review.project
        return super(ReviewJsonView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        return self.review.to_json()

    def post(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        if not self.review.creator_set.active().filter(user=request.user).exists():
            self.status = 403
            return {
                'errors': ['Only the owners of a Demo can edit it'],
                'review': self.review.to_json()
            }

        form = forms.ReviewQuickEditForm(request.POST)
        json_dict = {'errors': []}
        if form.is_valid():
            data = form.cleaned_data
            self.review.last_action_by = request.user
            update_fields = ['modified', 'last_action_by']
            for key, value in data.items():
                if value:
                    setattr(self.review, key, value)
                    update_fields.append(key)

            self.review.save(update_fields=update_fields)
        else:
            json_dict['errors'] = form.errors

        json_dict['review'] = self.review.to_json()
        return json_dict


class DeleteReviewAttachmentView(CanViewJsonView):

    status = 204

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(
            models.Review, pk=kwargs['review_pk'],
            creator__user=request.user,
            creator__active=True,
            state=constants.DRAFT
        )
        self.project = self.review.project
        return super(DeleteReviewAttachmentView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        ct = ContentType.objects.get(app_label='demotime', model='reviewrevision')
        attachment_pk = kwargs['attachment_pk']
        attachment = get_object_or_404(
            models.Attachment, pk=attachment_pk,
            content_type=ct, object_id=self.review.revision.pk
        )
        attachment.delete()
        return {
            'success': True,
        }


class ReviewSearchJsonView(JsonView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.projects = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.projects = self.request.user.projects
        if self.request.POST.get('project_pk'):
            self.projects = self.projects.filter(
                pk=self.request.POST['project_pk']
            )

        elif kwargs.get('proj_slug'):
            self.projects = self.projects.filter(
                slug=kwargs['proj_slug']
            )
        return super(ReviewSearchJsonView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        form = forms.ReviewFilterForm(
            self.projects,
            data=self.request.POST
        )
        if form.is_valid():
            reviews = form.get_reviews()
            review_json_dict = {
                'count': reviews.count(),
                'reviews': [],
            }
            for review in reviews:
                review_json_dict['reviews'].append(review.to_json())

            return review_json_dict

        return {'count': 0, 'reviews': []}


class DTRedirectView(RedirectView):

    permanent = True
    query_string = True
    pattern_name = 'review-detail'

    def get_redirect_url(self, *args, **kwargs):
        review = get_object_or_404(
            models.Review,
            pk=kwargs.get('pk')
        )
        kwargs['proj_slug'] = review.project.slug
        return super(DTRedirectView, self).get_redirect_url(*args, **kwargs)

# pylint: disable=invalid-name
create_review_view = CreateReviewView.as_view()
edit_review_form_view = EditReviewView.as_view()
review_detail = ReviewDetail.as_view()
reviewer_status_view = ReviewerStatusView.as_view()
review_state_view = ReviewStateView.as_view()
review_json_view = ReviewJsonView.as_view()
review_search_json_view = ReviewSearchJsonView.as_view()
review_list_view = ReviewListView.as_view()
dt_redirect_view = DTRedirectView.as_view()
delete_review_attachment_view = DeleteReviewAttachmentView.as_view()
