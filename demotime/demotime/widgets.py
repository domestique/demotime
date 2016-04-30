from itertools import chain

from django.forms import widgets
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from demotime import models


class MemberSelectRenderer(widgets.CheckboxFieldRenderer):
    inner_html = '<li>{choice_value}{sub_widgets} - {admin_choice_value}</li>'

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(MemberSelectRenderer, self).__init__(*args, **kwargs)

    # Yanked from lines 702-732 of django.forms.widgets
    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id')
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = self.__class__(
                    name=self.name,
                    value=self.value,
                    attrs=attrs_plus,
                    choices=choice_label,
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(format_html(self.inner_html, choice_value=choice_value,
                                          sub_widgets=sub_ul_renderer.render()))
            else:
                w = self.choice_input_class(self.name, self.value,
                                            self.attrs.copy(), choice, i)
                try:
                    pm = models.ProjectMember.objects.get(
                        user__pk=choice[0],
                        project=self.project
                    )
                except models.ProjectMember.DoesNotExist:
                    pm = None
                    is_admin = ''
                else:
                    is_admin = 'checked="checked"' if pm.is_admin else ''
                admin_choice_value = mark_safe(
                    '<label for="id_members_{}_admin">'
                    '<input type="checkbox" value="{}" name="adminmembers" id="id_adminmembers_{}_admin" {} />'
                    'Can Administer Project</label>'.format(
                        choice[0], choice[0], choice[0], is_admin
                    )
                )
                output.append(format_html(
                    self.inner_html,
                    choice_value=force_text(w),
                    sub_widgets='',
                    admin_choice_value=force_text(admin_choice_value),
                ))
        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class MemberSelectMultiple(widgets.CheckboxSelectMultiple):
    renderer = MemberSelectRenderer

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(MemberSelectMultiple, self).__init__(*args, **kwargs)

    def get_renderer(self, name, value, attrs=None, choices=()):
        """Returns an instance of the renderer."""
        if value is None:
            value = self._empty_value
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        return self.renderer(name, value, final_attrs, choices, project=self.project)
