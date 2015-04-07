from demotime import models


def unread_message_count(request):
    print request.user.is_authenticated()
    if request.user.is_authenticated():
        return {
            'unread_message_count': models.Message.objects.filter(
                receipient=request.user,
                read=False,
            ).count()
        }
    else:
        return {'unread_message_count': 0}


def has_unread_messages(request):
    if request.user.is_authenticated():
        return {
            'has_unread_messages': models.Message.objects.filter(
                receipient=request.user,
                read=False
            ).exists()
        }
    else:
        return {'has_unread_messages': False}
