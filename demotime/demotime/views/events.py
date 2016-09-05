from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models
from demotime.views import CanViewJsonView


class EventView(CanViewJsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        self.review = None
        return super(EventView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        json_data = {
            'errors': '',
            'status': 'success',
            'events': [],
        }
        events = models.Event.objects.filter(
            project=self.project
        )
        form = forms.EventFilterForm(project=self.project, data=request.GET)
        if form.is_valid():
            data = form.cleaned_data
            if data.get('review'):
                events = events.filter(review=data['review'])
            if data.get('event_type'):
                events = events.filter(event_type=data['event_type'])
        else:
            self.status = 400
            json_data['errors'] = form.errors
            return json_data

        for event in events:
            json_data['events'].append(event.to_json())

        return json_data
