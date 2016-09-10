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


class MessagesJsonView(JsonView):

    status = 200

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.review = None
        if 'review_pk' in kwargs:
            self.review = get_object_or_404(
                models.Review,
                pk=kwargs.get('review_pk'),
            )
            self.project = self.review.project
        return super(MessagesJsonView, self).dispatch(*args, **kwargs)

    def _format_json(self, bundles):
        json_data = {'message_count': bundles.count(), 'bundles': []}
        for bundle in bundles:
            msgs = bundle.message_set.filter(
                created__gte=bundle.modified
            ).select_related(
                'review',
                'thread',
            ).prefetch_related(
                'review__review',
                'review__review__project',
            )
            bundle_dict = {
                'bundle_pk': bundle.pk,
                'messages': [],
            }
            for msg in msgs:
                review_title = ''
                review_url = ''
                review_pk = ''
                is_comment = False
                thread_pk = ''
                if msg.review:
                    review_title = msg.review.review.title
                    review_url = msg.review.review.get_absolute_url()
                    review_pk = msg.review.review.pk

                if msg.thread:
                    is_comment = True
                    thread_pk = msg.thread.pk

                bundle_dict['messages'].append({
                    'review_url': review_url,
                    'review_title': review_title,
                    'review_pk': review_pk,
                    'is_comment': is_comment,
                    'thread_pk': thread_pk,
                    'message': msg.message,
                    'message_title': msg.title,
                    'message_pk': msg.pk,
                })
            json_data['bundles'].append(bundle_dict)
        return json_data

    def _get_review_messages(self):
        # Should only ever be one bundle, but lets keep our signatures
        # consistent eh?
        bundles = models.MessageBundle.objects.filter(
            review=self.review,
            owner=self.request.user,
            read=False,
            deleted=False,
        )
        return self._format_json(bundles)

    def _get_messages(self):
        bundles = models.MessageBundle.objects.filter(
            owner=self.request.user,
            read=False,
            deleted=False,
        )
        return self._format_json(bundles)

    def get(self, *args, **kwargs):
        if self.review:
            return self._get_review_messages()

        return self._get_messages()

    def post(self, *args, **kwargs):
        form = forms.BulkMessageUpdateForm(
            user=self.request.user,
            data=self.request.POST
        )
        if form.is_valid():
            if form.cleaned_data['mark_all_read']:
                messages = models.MessageBundle.objects.filter(
                    owner=self.request.user,
                )
            else:
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

        return self._get_messages()

inbox_view = InboxView.as_view()
msg_detail_view = MessageDetailView.as_view()
messages_json_view = MessagesJsonView.as_view()
