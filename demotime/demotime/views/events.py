from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404

from demotime import forms, models
from demotime.views import CanViewJsonView


class EventView(CanViewJsonView):

    status = 200
    paginate_by = 25

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
            project=self.project
        )
        form = forms.EventFilterForm(project=self.project, data=request.GET)
        if form.is_valid():
            data = form.cleaned_data
            if data.get('review'):
                events = events.filter(review=data['review'])
            if data.get('event_type'):
                events = events.filter(
                    event_type__in=data['event_type']
                )
            if data.get('exclude_type'):
                events = events.exclude(
                    event_type__in=data['exclude_type']
                )
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
        paginator = Paginator(events, self.paginate_by)
        page = request.GET.get('page')
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            page = 1
            events = paginator.page(page)
        except EmptyPage:
            page = paginator.num_pages
            events = paginator.page(page)

        for event in events:
            json_data['events'].append(event.to_json())

        json_data['page'] = page
        json_data['page_count'] = paginator.num_pages
        json_data['count'] = paginator.count
        return json_data
