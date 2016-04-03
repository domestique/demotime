from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from demotime import forms, models
from . import JsonView


class InboxView(ListView):
    template_name = 'demotime/inbox.html'
    paginate_by = 15

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InboxView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.BulkMessageUpdateForm(user=request.user, data=request.POST)
        if form.is_valid():
            messages = form.cleaned_data['messages']
            action = form.cleaned_data['action']
            if action == form.READ:
                messages.update(read=True)
            elif action == form.UNREAD:
                messages.update(read=False)
            elif action == form.DELETED:
                messages.update(deleted=True)
            elif action == form.UNDELETED:
                messages.update(deleted=False)

            return redirect('inbox')
        else:
            return self.get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = models.MessageBundle.objects.filter(owner=self.request.user)
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

    def get_context_data(self, *args, **kwargs):
        context = super(InboxView, self).get_context_data(*args, **kwargs)
        context['form'] = forms.BulkMessageUpdateForm(user=self.request.user)

        return context


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

        self.message = get_object_or_404(
            models.MessageBundle,
            pk=self.kwargs.get(self.pk_url_kwarg),
            owner=self.request.user
        )
        self.message.read = read
        self.message.deleted = delete
        self.message.save(update_fields=['read', 'deleted'])

        return self.message

    def get(self, *args, **kwargs):
        response = super(MessageDetailView, self).get(*args, **kwargs)
        if self.redirect:
            return redirect('inbox')
        else:
            return response

    def get_context_data(self, **kwargs):
        context = super(MessageDetailView, self).get_context_data(**kwargs)
        msg = context['object']
        try:
            next_msg = msg.get_next_by_created(
                owner=self.message.owner,
                read=False
            )
        except models.MessageBundle.DoesNotExist:
            next_msg = None

        try:
            prev_msg = msg.get_previous_by_created(
                owner=self.message.owner,
                read=False
            )
        except models.MessageBundle.DoesNotExist:
            prev_msg = None

        context['next_msg'] = next_msg
        context['prev_msg'] = prev_msg
        return context


class MessageCountJsonView(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = None
        if 'review_pk' in kwargs:
            self.review = get_object_or_404(
                models.Review,
                pk=kwargs.get('review_pk'),
            )
        return super(MessageCountJsonView, self).dispatch(*args, **kwargs)

    def _get_review_message_count(self):
        # Should only ever be one bundle, but lets keep our signatures
        # consistent eh?
        bundles = models.MessageBundle.objects.filter(
            review=self.review,
            owner=self.request.user,
            read=False,
            deleted=False,
        ).count()
        return {
            'message_count': bundles,
        }

    def _get_message_count(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.request.user,
            read=False,
            deleted=False,
        ).count()
        return {
            'message_count': bundles,
        }

    def get(self, *args, **kwargs):
        if self.review:
            return self._get_review_message_count()

        return self._get_message_count()

inbox_view = InboxView.as_view()
msg_detail_view = MessageDetailView.as_view()
message_count_json_view = MessageCountJsonView.as_view()
