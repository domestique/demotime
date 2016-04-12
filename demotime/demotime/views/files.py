import os

from django.conf import settings
from django.views import static
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from sendfile import sendfile


class UserMedia(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserMedia, self).dispatch(*args, **kwargs)

    def get(self, request, file_path):
        if settings.SENDFILE_BACKEND or settings.DT_PROD:
            full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            return sendfile(request, full_file_path, attachment=False)
        else:
            return static.serve(request, file_path, document_root=settings.MEDIA_ROOT)


user_media_view = UserMedia.as_view()
