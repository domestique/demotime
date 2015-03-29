from django.shortcuts import redirect
from django.forms import formset_factory
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models


class IndexView(TemplateView):
    template_name = 'demotime/index.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['open_demos'] = models.Review.objects.filter(
            creator=self.request.user,
            status=models.Review.OPEN,
        )
        context['open_reviews'] = models.Review.objects.filter(
            reviewers=self.request.user,
            status=models.Review.OPEN,
        )
        # TODO: Figure out how to show the recently updated ones
        context['updated_demos'] = []
        return context


class ReviewDetail(DetailView):
    template_name = 'demotime/review.html'
    model = models.Review

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.comment = models.Comment(
            review=self.get_object().revision,
            commenter=self.request.user
        )
        AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=3, max_num=3)
        self.attachment_forms = AttachmentFormSet()
        self.comment_form = None
        return super(ReviewDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
        context['comment_form'] = self.comment_form if self.comment_form else forms.CommentForm(instance=self.comment)
        context['attachment_forms'] = self.attachment_forms
        return context

    def post(self, request, *args, **kwargs):
        self.comment_form = forms.CommentForm(data=request.POST, instance=self.comment)
        AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=3, max_num=3)
        self.attachment_forms = AttachmentFormSet(data=request.POST, files=request.FILES)
        data = {}
        if self.comment_form.is_valid():
            data = self.comment_form.cleaned_data
        else:
            return self.get(request, *args, **kwargs)

        if self.attachment_forms.is_valid():
            data['attachments'] = []
            for form in self.attachment_forms.forms:
                if form.cleaned_data:
                    data['attachments'].append({
                        'attachment': form.cleaned_data['attachment'],
                        'attachment_type': form.cleaned_data['attachment_type'],
                    })

        obj = self.get_object()
        data['commenter'] = self.request.user
        data['review'] = obj.revision
        models.Comment.create_comment(**data)
        return redirect(reverse('review-detail', kwargs={'pk': obj.pk}))


class CreateReviewView(TemplateView):
    template_name = 'demotime/create_review.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CreateReviewView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.review_inst = models.Review(creator=self.request.user)
        self.review_form = forms.ReviewForm(
            user=self.request.user,
            instance=self.review_inst,
            data=request.POST
        )
        AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=3, max_num=3)
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
                    })

            models.Review.create_review(**data)

            return redirect('index')
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            # If we're using this method as the POST error path, let's
            # preserve the existing forms. Also, maybe this is dumb?
            self.review_inst = models.Review(creator=self.request.user)
            self.review_form = forms.ReviewForm(
                user=self.request.user,
                instance=self.review_inst
            )
            AttachmentFormSet = formset_factory(forms.AttachmentForm, extra=3, max_num=3)
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


index_view = IndexView.as_view()
review_form_view = CreateReviewView.as_view()
review_detail = ReviewDetail.as_view()
