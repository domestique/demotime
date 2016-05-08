from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect

from demotime import constants, forms, models
from demotime.views import CanViewMixin, JsonView


class GroupListView(CanViewMixin, ListView):

    model = models.Group
    template = 'demotime/group_list.html'
    require_superuser_privileges = True
    project = None


group_list = GroupListView.as_view()
