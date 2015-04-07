from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import models


class InboxView(ListView):
    template_name = 'demotime/inbox.html'
    paginate_by = 15

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InboxView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = models.Message.objects.filter(receipient=self.request.user)
        _filter = self.request.GET.get('filter')
        sort = self.request.GET.get('sort')
        if _filter == 'read':
            queryset = queryset.filter(read=True, deleted=False)
        elif _filter == 'deleted':
            queryset = queryset.filter(deleted=True)
        else:
            queryset = queryset.filter(read=False, deleted=False)

        if sort == 'newest':
            queryset = queryset.order_by('-created')
        elif sort == 'oldest':
            queryset = queryset.order_by('created')

        return queryset


class MessageDetailView(DetailView):
    template_name = 'demotime/message.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MessageDetailView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        read = True
        delete = False
        self.redirect = False
        action = self.request.GET.get('action')
        if action == 'mark-unread':
            read = False
            self.redirect = True
        elif action == 'delete':
            delete = True
            self.redirect = True

        message = get_object_or_404(
            models.Message,
            pk=self.kwargs.get(self.pk_url_kwarg),
            receipient=self.request.user
        )
        message.read = read
        message.deleted = delete
        message.save(update_fields=['read', 'deleted'])

        return message

    def get(self, *args, **kwargs):
        response = super(MessageDetailView, self).get(*args, **kwargs)
        if self.redirect:
            return redirect('inbox')
        else:
            return response

inbox_view = InboxView.as_view()
msg_detail_view = MessageDetailView.as_view()
