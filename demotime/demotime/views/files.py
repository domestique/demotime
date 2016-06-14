import os
import re

from django.conf import settings
from django.views import static
from django.views.generic.base import View
from django.shortcuts import get_object_or_404

from demotime import models
from demotime.views import CanViewMixin

from sendfile import sendfile


class UserMedia(CanViewMixin, View):

    def dispatch(self, *args, **kwargs):
        self.attachment = get_object_or_404(
            models.Attachment,
            pk=kwargs.pop('pk')
        )
        self.project = self.attachment.project
        return super(UserMedia, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        file_path = self.attachment.attachment.name
        if settings.SENDFILE_BACKEND or settings.DT_PROD:
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            return sendfile(request, full_file_path, attachment=False)
        else:
            return static.serve(request, file_path, document_root=settings.MEDIA_ROOT)


user_media_view = UserMedia.as_view()
