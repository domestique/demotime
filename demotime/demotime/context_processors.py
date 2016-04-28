from django.conf import settings
from django.db.models import Q

from demotime import models


def unread_message_count(request):
    if request.user.is_authenticated():
        return {
            'unread_message_count': models.MessageBundle.objects.filter(
                owner=request.user,
                read=False,
                deleted=False,
            ).count()
        }
    else:
        return {'unread_message_count': 0}


def has_unread_messages(request):
    if request.user.is_authenticated():
        return {
            'has_unread_messages': models.MessageBundle.objects.filter(
                owner=request.user,
                read=False,
                deleted=False,
            ).exists()
        }
    else:
        return {'has_unread_messages': False}


def site_settings(request):
    return {'site_settings': settings}


def available_projects(request):
    projects = models.Project.objects.filter(
        # Direct Membership
        Q(projectmember__user=request.user) |
        # Group Membership
        Q(projectgroup__group__groupmember__user=request.user)
    )
    return {'available_projects': projects}
