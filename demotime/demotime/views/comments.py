import json

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
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        self.revision = get_object_or_404(
            models.ReviewRevision,
            number=self.kwargs.get('rev_num'),
            review__pk=self.kwargs.get('review_pk'),
        )
        self.review = self.revision.review
        return super(CommentJsonView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'comment_pk' in request.GET:
            try:
                comment = models.Comment.objects.get(pk=request.GET['comment_pk'])
            except models.Comment.DoesNotExist:
                self.status = 400
                return {
                    'errors': 'Comment does not exist',
                    'status': 'failure',
                    'comment': {}
                }
            else:
                return {
                    'errors': '',
                    'status': 'success',
                    'comment': comment.to_json(),
                }

        json_data = {
            'errors': '',
            'status': 'success',
            'threads': {}
        }
        for thread in self.revision.commentthread_set.all():
            comment_data = []
            for comment in thread.comment_set.all():
                comment_data.append(comment.to_json())

            json_data['threads'][thread.pk] = comment_data

        return json_data

    def post(self, request, *args, **kwargs):
        thread = None
        if 'thread' in request.POST:
            try:
                thread = models.CommentThread.objects.get(pk=request.POST['thread'])
            except models.CommentThread.DoesNotExist:
                self.status = 400
                return {
                    'errors': 'Comment Thread {} does not exist'.format(request.POST['thread']),
                    'status': 'failure',
                    'comment': {}
                }

        comment_form = forms.UpdateCommentForm(
            data=request.POST, files=request.FILES, thread=thread
        )
        if comment_form.is_valid():
            data = comment_form.cleaned_data
            comment = models.Comment.create_comment(
                commenter=request.user,
                comment=data['comment'],
                review=self.revision,
                thread=thread,
                attachment=data['attachment'],
                description=data.get('description', '')
            )
            return {
                'errors': '',
                'status': 'success',
                'comment': comment.to_json(),
            }

        return {
            'errors': comment_form.errors,
            'status': 'failure',
            'comment': {},
        }

    def patch(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            self.status = 400
            return {
                'errors': 'Improperly formed json request',
                'status': 'failure',
                'comment': {}
            }

        try:
            comment = models.Comment.objects.get(pk=body.get('comment_pk'))
        except models.Comment.DoesNotExist:
            self.status = 400
            return {
                'errors': 'Comment {} does not exist'.format(body.get('comment_pk')),
                'status': 'failure',
                'comment': {}
            }

        body['thread'] = comment.thread.pk
        comment_form = forms.UpdateCommentForm(
            data=body, files=request.FILES,
            thread=comment.thread, instance=comment,
        )
        if comment_form.is_valid():
            data = comment_form.cleaned_data
            comment.comment = data['comment']
            comment.save(update_fields=['modified', 'comment'])
            if data.get('attachment'):
                models.Attachment.create_attachment(
                    attachment=data['attachment'],
                    description=data.get('description', ''),
                    content_object=self.comment,
                )

            if body.get('delete_attachments'):
                for pk in body['delete_attachments']:
                    try:
                        attachment = comment.attachments.get(pk=pk)
                    except models.Attachment.DoesNotExist:
                        pass
                    else:
                        attachment.delete()
            return {
                'status': 'success',
                'errors': '',
                'comment': comment.to_json()
            }

        return {
            'status': 'failure',
            'errors': comment_form.errors,
            'comment': {}
        }


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
            self.comment.save(update_fields=['modified', 'comment'])
            if data.get('attachment'):
                models.Attachment.create_attachment(
                    attachment=data['attachment'],
                    description=data.get('description', ''),
                    content_object=self.comment,
                )
            return redirect(self.comment.thread.review_revision.get_absolute_url())
        else:
            return self.get(*args, **kwargs)

comments_json_view = CommentJsonView.as_view()
update_comment_view = UpdateCommentView.as_view()
delete_comment_attachment_view = DeleteCommentAttachmentView.as_view()
