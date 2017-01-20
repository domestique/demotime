from django.conf import settings

from demotime import models


def site_settings(request):
    return {'site_settings': settings}


def available_projects(request):
    if not request.user.is_authenticated:
        return {'available_projects': models.Project.objects.none()}

    return {'available_projects': request.user.projects}
