import json
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime.views import JsonView


class GIFSearch(JsonView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GIFSearch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q')
        if not search_term:
            return {}

        try:
            response = requests.get(
                settings.GIF_PROVIDER_URL,
                params={
                    'q': search_term.replace(' ', '+'),
                    'api_key': settings.GIF_PROVIDER_API_KEY
                }
            )
        except: # Naughty bare except, but I ain't taking chances here
            content = {
                'error': 'Failed to communicate with GIF service',
                'status': 'failed'
            }
        else:
            if response.status_code == 200:
                data = json.loads(response.content.decode('utf-8'))
                content = {
                    'error': '',
                    'status': 'success',
                    'data': data.get('data', {})
                }
            else:
                content = {
                    'error': 'Bad response from GIF service',
                    'status': 'failed',
                    'data': {}
                }

        return content
