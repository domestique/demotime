from django.shortcuts import get_object_or_404, redirect
from django.forms import formset_factory
from django.views.generic import TemplateView, DetailView, ListView, RedirectView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType

from demotime import forms, models
from demotime.views import CanViewMixin
from . import JsonView


class ReviewDetail(CanViewMixin, DetailView):
    template_name = 'demotime/review.html'
    model = models.Review

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        if self.kwargs.get('rev_num'):
            self.revision = get_object_or_404(
                models.ReviewRevision,
                number=self.kwargs['rev_num'],
                review__pk=self.kwargs['pk']
            )
        else:
            self.revision = self.get_object().revision

        self.review = self.revision.review
        self.comment = models.Comment(
            commenter=self.request.user
        )
        self.attachment_form = None
        self.comment_form = None
        models.MessageBundle.objects.filter(
            owner=request.user,
            review=self.revision.review
        ).update(read=True)
        return super(ReviewDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
        try:
            reviewer = models.Reviewer.objects.get(
                review=self.revision.review,
                reviewer=self.request.user
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

        if self.request.user == self.revision.review.creator:
            context['review_state_form'] = forms.ReviewStateForm(
                self.request.user,
                self.revision.review.pk,
                initial={'review': self.revision.review}
            )

        if self.revision.review.reviewer_set.filter(reviewer=self.request.user).exists():
            context['reviewer'] = self.revision.review.reviewer_set.get(
                reviewer=self.request.user
            )

        models.UserReviewStatus.objects.filter(
            review=self.revision.review,
            user=self.request.user,
        ).update(read=True)
        context['project'] = self.project
        context['revision'] = self.revision
        context['comment_form'] = self.comment_form if self.comment_form else forms.CommentForm(instance=self.comment)
        context['attachment_form'] = self.attachment_form if self.attachment_form else forms.AttachmentForm()
        return context

    def post(self, request, *args, **kwargs):
        thread = None
        if request.POST.get('thread'):
            if self.revision.commentthread_set.filter(
                    pk=request.POST.get('thread')
            ):
                thread = models.CommentThread.objects.get(pk=request.POST['thread'])

        self.comment_form = forms.CommentForm(thread=thread, data=request.POST, instance=self.comment)
        self.attachment_form = forms.AttachmentForm(data=request.POST, files=request.FILES)
        data = {}
        if self.comment_form.is_valid():
            data = self.comment_form.cleaned_data
        else:
            return self.get(request, *args, **kwargs)

        if self.attachment_form.is_valid():
            data.update(self.attachment_form.cleaned_data)

        obj = self.get_object()
        data['commenter'] = self.request.user
        data['review'] = obj.revision
        models.Comment.create_comment(**data)
        return redirect(obj.get_absolute_url())


class CreateReviewView(TemplateView):
    template_name = 'demotime/create_review.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            self.review_inst = get_object_or_404(models.Review, pk=kwargs['pk'])
            self.project = self.review_inst.project
            self.template_name = 'demotime/edit_review.html'
        else:
            self.review_inst = models.Review(creator=self.request.user)
            self.project = None
        return super(CreateReviewView, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk=None, *args, **kwargs):
        self.review_form = forms.ReviewForm(
            user=self.request.user,
            instance=self.review_inst,
            data=request.POST
        )
        AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=10, max_num=25)
        self.attachment_forms = AttachmentFormSet(data=request.POST, files=request.FILES)
        if self.review_form.is_valid() and self.attachment_forms.is_valid():
            data = self.review_form.cleaned_data
            data['creator'] = request.user
            data['attachments'] = []
            for form in self.attachment_forms.forms:
                if form.cleaned_data:
                    data['attachments'].append({
                        'attachment': form.cleaned_data['attachment'],
                        'attachment_type': form.cleaned_data['attachment_type'],
                        'description': form.cleaned_data['description'],
                    })

            if pk:
                review = models.Review.update_review(self.review_inst.pk, **data)
            else:
                review = models.Review.create_review(**data)

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
            if pk:
                self.review_inst = get_object_or_404(models.Review, pk=pk)
                self.template_name = 'demotime/edit_review.html'
            else:
                self.review_inst = models.Review(creator=self.request.user)
            self.review_form = forms.ReviewForm(
                user=self.request.user,
                instance=self.review_inst,
                initial={'description': ''},
            )
            AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=10, max_num=25)
            self.attachment_forms = AttachmentFormSet()
        return super(CreateReviewView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateReviewView, self).get_context_data(**kwargs)
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
        form = forms.ReviewFilterForm(self.request.GET)
        if form.is_valid():
            return form.get_reviews(qs)

        return models.Review.objects.none()

    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        initial = self.request.GET.copy()
        initial['state'] = initial.get('state', models.reviews.OPEN)
        context.update({
            'form': forms.ReviewFilterForm(initial=initial)
        })
        return context


class ReviewerStatusView(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        reviewer_pk = kwargs['reviewer_pk']
        self.reviewer = get_object_or_404(
            models.Reviewer, pk=reviewer_pk, reviewer=self.request.user
        )
        self.review = self.reviewer.review
        self.project = self.review.project
        return super(ReviewerStatusView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
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


class ReviewStateView(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        review_pk = kwargs['pk']
        self.review = get_object_or_404(models.Review, pk=review_pk)
        self.project = self.review.project
        return super(ReviewStateView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        form = forms.ReviewStateForm(
            self.request.user, self.review.pk, data=self.request.POST
        )
        if form.is_valid():
            changed = self.review.update_state(form.cleaned_data['state'])
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


class DeleteCommentAttachmentView(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteCommentAttachmentView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ct = ContentType.objects.get(app_label='demotime', model='comment')
        attachment_pk = kwargs['attachment_pk']
        comment_pk = kwargs['comment_pk']
        comment = get_object_or_404(
            models.Comment, pk=comment_pk, commenter=request.user
        )
        attachment = get_object_or_404(
            models.Attachment, pk=attachment_pk,
            content_type=ct, object_id=comment.pk
        )
        if request.POST.get('delete') == 'true':
            attachment.delete()
            return {
                'success': True,
            }

        return {}


class UpdateCommentView(DetailView):

    model = models.Comment
    template_name = 'demotime/edit_comment.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        comment_pk = kwargs['pk']
        self.comment = get_object_or_404(
            models.Comment, pk=comment_pk, commenter=self.request.user
        )
        return super(UpdateCommentView, self).dispatch(request, *args, **kwargs)

    def init_form(self, data=None, files=None):
        kwargs = {}
        if data:
            kwargs['data'] = data
        if files:
            kwargs['files'] = files
        return forms.UpdateCommentForm(instance=self.comment, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateCommentView, self).get_context_data(**kwargs)
        context['form'] = self.comment_form
        return context

    def get(self, *args, **kwargs):
        if not hasattr(self, 'comment_form'):
            self.comment_form = self.init_form()
        return super(UpdateCommentView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.comment_form = self.init_form(self.request.POST, self.request.FILES)
        if self.comment_form.is_valid():
            data = self.comment_form.cleaned_data
            self.comment.comment = data['comment']
            self.comment.save(update_fields=['comment'])
            if data.get('attachment'):
                models.Attachment.objects.create(
                    attachment=data['attachment'],
                    attachment_type=data['attachment_type'],
                    description=data.get('description', ''),
                    content_object=self.comment,
                )
            return redirect(self.comment.thread.review_revision.get_absolute_url())
        else:
            return self.get(*args, **kwargs)


class ReviewJsonView(JsonView):

    def dispatch(self, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=kwargs['proj_slug']
        )
        self.review = None
        return super(ReviewJsonView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        form = forms.ReviewFilterForm(self.request.POST)
        if form.is_valid():
            reviews = form.get_reviews()
            review_json_dict = {
                'count': reviews.count(),
                'reviews': [],
            }
            for review in reviews:
                review_dict = {
                    'title': review.title,
                    'url': review.get_absolute_url(),
                    'creator': review.creator.userprofile.name,
                    'state': review.state,
                    'reviewer_state': review.reviewer_state,
                    'pk': review.pk,
                    'reviewing_count': review.reviewing_count,
                    'approved_count': review.approved_count,
                    'rejected_count': review.rejected_count,
                    'reviewers': [],
                    'followers': [],
                }
                for reviewer in review.reviewer_set.all():
                    review_dict['reviewers'].append({
                        'name': reviewer.reviewer.userprofile.name,
                        'user_pk': reviewer.reviewer.pk,
                        'reviewer_status': reviewer.status,
                    })

                for follower in review.follower_set.all():
                    review_dict['followers'].append({
                        'name': follower.user.userprofile.name,
                        'user_pk': follower.user.pk,
                    })

                review_json_dict['reviews'].append(review_dict)

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

review_form_view = CreateReviewView.as_view()
review_detail = ReviewDetail.as_view()
reviewer_status_view = ReviewerStatusView.as_view()
review_state_view = ReviewStateView.as_view()
review_json_view = ReviewJsonView.as_view()
update_comment_view = UpdateCommentView.as_view()
delete_comment_attachment_view = DeleteCommentAttachmentView.as_view()
review_list_view = ReviewListView.as_view()
dt_redirect_view = DTRedirectView.as_view()
