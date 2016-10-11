from django.shortcuts import get_object_or_404

from demotime import constants, forms, models
from demotime.views import CanViewJsonView


class EventView(CanViewJsonView):

    status = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = None
        self.review = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            models.Project,
            slug=self.kwargs['proj_slug']
        )
        if request.GET.get('review', ''):
            self.review = get_object_or_404(
                models.Review,
                pk=request.GET['review']
            )
        return super(EventView, self).dispatch(request, *args, **kwargs)

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        json_data = {
            'errors': '',
            'status': 'success',
            'events': [],
        }
        events = models.Event.objects.filter(
            project=self.project,
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

        events = events.select_related(
            'project', 'review', 'user',
            'user__userprofile',
        ).prefetch_related(
            'related_object',
        )
        for event in events:
            json_data['events'].append(event.to_json())

        return json_data
