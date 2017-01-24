
from django.shortcuts import get_object_or_404
from demotime import forms, models
from demotime.views import CanViewJsonView


class ReactionJsonView(CanViewJsonView):

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
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, reaction_pk, *args, **kwargs): # pylint: disable=unused-argument
        reaction = get_object_or_404(
            models.Reaction,
            pk=reaction_pk
        )
        if reaction.user != request.user:
            self.status = 400
            return {
                'status': 'failure',
                'errors': {
                    'user': "User can not delete reaction they don't own."
                },
                'reaction': reaction.to_json(),
            }
        else:
            reaction.delete()
            return {
                'status': 'success',
                'errors': {},
                'reaction': None,
            }

    def get(self, request, *args, **kwargs): # pylint: disable=unused-argument
        reactions = models.Reaction.objects.all()
        form = forms.ReactionFilterForm(request.GET)
        if form.is_valid():
            filter_data = {}
            for key, val in form.cleaned_data.items():
                if val:
                    filter_data[key] = val

            reactions = reactions.filter(**filter_data)
            return {
                'status': 'success',
                'errors': {},
                'reactions': [reaction.to_json() for reaction in reactions]
            }
        else:
            self.status = 400
            return {
                'status': 'failure',
                'errors': form.errors,
                'reactions': []
            }

    def post(self, request, *args, **kwargs): # pylint: disable=unused-argument
        form = forms.ReactionForm(request.POST)
        if form.is_valid():
            review = form.cleaned_data['review']
            reaction_type = form.cleaned_data['reaction_type']
            reaction_object = form.cleaned_data['reaction_object']
            react_kwargs = {
                'project': self.project, 'review': review,
                'reaction_type': reaction_type, 'user': request.user,
            }
            react_kwargs[form.cleaned_data['object_type']] = reaction_object
            reaction = models.Reaction.create_reaction(**react_kwargs)
            self.status = 201
            return {
                'status': 'success',
                'errors': {},
                'reaction': reaction.to_json()
            }
        else:
            self.status = 400
            return {
                'status': 'failure',
                'errors': form.errors,
                'reaction': {},
            }
