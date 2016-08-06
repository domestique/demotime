from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models
from . import CanViewJsonView


class CommentJsonView(CanViewJsonView):

    status = 200

    @method_decorator(login_required)
    def disptach(self, request, *args, **kwargs):
        return super(CommentJsonView, self).dispatch(request, *args, **kwargs)


class DeleteCommentAttachmentView(CanViewJsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        comment_pk = kwargs['comment_pk']
        self.comment = get_object_or_404(
            models.Comment, pk=comment_pk, commenter=request.user
        )
        self.review = self.comment.thread.review_revision.review
        self.project = self.review.project
        return super(DeleteCommentAttachmentView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ct = ContentType.objects.get(app_label='demotime', model='comment')
        attachment_pk = kwargs['attachment_pk']
        attachment = get_object_or_404(
            models.Attachment, pk=attachment_pk,
            content_type=ct, object_id=self.comment.pk
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

comments_json_view = CommentJsonView.as_view()
update_comment_view = UpdateCommentView.as_view()
delete_comment_attachment_view = DeleteCommentAttachmentView.as_view()
