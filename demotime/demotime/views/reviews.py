from django.shortcuts import get_object_or_404, redirect
from django.forms import formset_factory
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models


class ReviewDetail(DetailView):
    template_name = 'demotime/review.html'
    model = models.Review

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('rev_pk'):
            self.revision = get_object_or_404(
                models.ReviewRevision, pk=self.kwargs['rev_pk']
            )
        else:
            self.revision = self.get_object().revision

        self.comment = models.Comment(
            commenter=self.request.user
        )
        self.attachment_form = None
        self.comment_form = None
        return super(ReviewDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
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
        return super(CreateReviewView, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk=None, *args, **kwargs):
        if pk:
            self.review_inst = get_object_or_404(models.Review, pk=pk)
            self.template_name = 'demotime/edit_review.html'
        else:
            self.review_inst = models.Review(creator=self.request.user)
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
                pk=review.pk,
                rev_pk=review.revision.pk
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
            'review_form': self.review_form,
            'review_inst': self.review_inst,
            'attachment_forms': self.attachment_forms
        })
        return context

review_form_view = CreateReviewView.as_view()
review_detail = ReviewDetail.as_view()
