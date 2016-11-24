import re
import json

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models
from demotime.views import CanViewJsonView


class CommentJsonView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.revision = None
        self.review = None

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

    def get(self, request, *args, **kwargs): # pylint: disable=unused-argument
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

    def _process_attachments(self, post_data=None):
        post_data = post_data or self.request.POST
        attachment_forms = []
        file_keys = self.request.FILES.keys()
        search_str = r'(\d+-)?attachment'
        form_count = 0
        for key in file_keys:
            match = re.search(search_str, key)
            if match:
                prefix = re.search(r'(\d+)?', key).group()
                attachment_forms.append((
                    forms.CommentAttachmentForm(
                        data=post_data,
                        files=self.request.FILES,
                        prefix=prefix
                    ),
                    prefix
                ))
                form_count += 1

        attachments = []
        if all(form.is_valid() for form, prefix in attachment_forms):
            for form, prefix in attachment_forms:
                data = form.cleaned_data
                attachments.append({
                    'attachment': data['attachment'],
                    'description': data['description'],
                    'sort_order': prefix,
                })

        return attachments

    def post(self, request, *args, **kwargs): # pylint: disable=unused-argument
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

        attachments = self._process_attachments()
        has_attachments = True if attachments else False
        comment_form = forms.CommentForm(
            thread=thread, data=request.POST, has_attachments=has_attachments
        )
        if comment_form.is_valid():
            data = comment_form.cleaned_data
            comment = models.Comment.create_comment(
                commenter=request.user,
                comment=data['comment'],
                review=self.revision,
                thread=thread,
                attachments=attachments,
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

    def patch(self, request, *args, **kwargs): # pylint: disable=unused-argument
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
        attachments = self._process_attachments(post_data=body)
        has_attachments = True if attachments else False
        comment_form = forms.CommentForm(
            data=body, files=request.FILES,
            thread=comment.thread, instance=comment,
            has_attachments=has_attachments
        )
        if body.get('delete_attachments'):
            for pk in body['delete_attachments']:
                try:
                    attachment = comment.attachments.get(pk=pk)
                except models.Attachment.DoesNotExist:
                    pass
                else:
                    attachment.delete()

        if comment_form.is_valid():
            data = comment_form.cleaned_data
            comment.comment = data['comment']
            comment.save(update_fields=['modified', 'comment'])
            for count, attachment in enumerate(attachments):
                models.Attachment.create_attachment(
                    attachment=data['attachment'],
                    description=data.get('description', ''),
                    content_object=self.comment,
                    sort_order=attachment.get('sort_order') or count
                )

        if 'comment' not in request.POST or comment_form.is_valid():
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comment = None
        self.review = None
        self.project = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        comment_pk = kwargs['comment_pk']
        self.comment = get_object_or_404(
            models.Comment, pk=comment_pk, commenter=request.user
        )
        self.review = self.comment.thread.review_revision.review
        self.project = self.review.project
        return super(DeleteCommentAttachmentView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs): # pylint: disable=unused-argument
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


comments_json_view = CommentJsonView.as_view()
delete_comment_attachment_view = DeleteCommentAttachmentView.as_view()
