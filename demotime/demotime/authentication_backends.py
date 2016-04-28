from django.contrib.auth.backends import ModelBackend

from demotime.models import UserProxy


class UserProxyModelBackend(ModelBackend):

    def get_user(self, user_id):
        try:
            return UserProxy.objects.get(pk=user_id)
        except UserProxy.DoesNotExist:
            return None
