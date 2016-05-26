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
        file_path = kwargs['file_path']
        pk_search = re.search('\d+', file_path)
        pk = pk_search.group() if pk_search else None
        self.review = get_object_or_404(
            models.Review,
            pk=pk,
        )
        self.project = self.review.project
        return super(UserMedia, self).dispatch(*args, **kwargs)

    def get(self, request, file_path):
        if settings.SENDFILE_BACKEND or settings.DT_PROD:
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            return sendfile(request, full_file_path, attachment=False)
        else:
            return static.serve(request, file_path, document_root=settings.MEDIA_ROOT)


user_media_view = UserMedia.as_view()
