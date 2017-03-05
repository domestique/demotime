from django import http
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models
from demotime.views import CanViewJsonView


class AttachmentsJsonView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.revision = None
        self.review = None
        self.attachment = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(
            models.Review,
            pk=self.kwargs['review_pk']
        )
        if self.kwargs.get('attachment_pk'):
            self.attachment = get_object_or_404(
                models.Attachment,
                pk=self.kwargs['attachment_pk']
            )
        self.project = self.review.project
        return super(AttachmentsJsonView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs): # pylint: disable=unused-argument
        return {
            'status': 'success',
            'errors': [],
            'attachment': self.attachment.to_json()
        }

    def delete(self, *args, **kwargs): # pylint: disable=unused-argument
        self.attachment.delete()
        self.status = 204
        return ''

    def post(self, request, *args, **kwargs):
        if self.attachment:
            return http.HttpResponseBadRequest('')

        form = forms.AttachmentForm(request.POST)
        if form.is_valid():
            if not request.FILES:
                self.status = 400
                return {
                    'status': 'failure',
                    'errors': {'files': ['No files provided for attaching']}
                }
            obj = form.cleaned_data['object']
            max_sort_order = obj.attachments.aggregate(
                Max('sort_order')
            )['sort_order__max'] or 0
            sort_start = max_sort_order + 1
            attachments = []
            for count, upload in enumerate(request.FILES.getlist('files'), sort_start):
                attachment = models.Attachment.create_attachment(
                    attachment=upload,
                    content_object=obj,
                    sort_order=count,
                )
                attachments.append(attachment.to_json())
            self.status = 201
            return {
                'status': 'success',
                'errors': [],
                'attachments': attachments,
            }
        else:
            self.status = 400
            return {
                'status': 'failure',
                'errors': form.errors,
            }
        return super().post(request, *args, **kwargs)


attachments_json_view = AttachmentsJsonView.as_view()
