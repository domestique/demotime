from django.conf import settings
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from sendfile import sendfile


class UserMedia(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserMedia, self).dispatch(*args, **kwargs)

    def get(self, request, file_path):
        full_file_path = '{}/{}'.format(settings.MEDIA_ROOT, file_path)
        return sendfile(request, full_file_path, attachment=False)


user_media_view = UserMedia.as_view()
