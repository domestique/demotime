import ast

from django.db import models
from django.conf import settings

from demotime.models.base import BaseModel


class SettingManager(models.Manager):

    def get_value(self, key, default=None):
        try:
            obj = self.get(key=key)
        except self.model.DoesNotExist:
            if settings.DEBUG:
                raise
            else:
                return default
        else:
            return obj.value if obj.active else default


class Setting(BaseModel):

    LIST = 'list'
    BOOL = 'bool'
    DICT = 'dict'
    STRING = 'string'
    INT = 'int'

    SWITCH_TYPES = (
        (LIST, 'List'),
        (BOOL, 'Boolean'),
        (DICT, 'Dictionary'),
        (STRING, 'String'),
        (INT, 'Integer'),
    )

    title = models.CharField(max_length=128)
    key = models.SlugField(max_length=128, db_index=True)
    description = models.TextField(blank=True)
    raw_value = models.TextField()
    setting_type = models.CharField(
        max_length=32,
        choices=SWITCH_TYPES,
        db_index=True
    )
    active = models.BooleanField(default=False)

    objects = SettingManager()

    def __str__(self):
        return 'Setting: {}'.format(self.title)

    @classmethod
    def create_setting(cls, title, key, raw_value, setting_type,
                       description='', active=False):
        return cls.objects.create(
            title=title,
            key=key,
            description=description,
            raw_value=raw_value,
            setting_type=setting_type,
            active=active
        )

    def _value_dict(self):
        return ast.literal_eval(self.raw_value)

    def _value_list(self):
        if self.raw_value.startswith('[') and self.raw_value.endswith(']'):
            return tuple(ast.literal_eval(self.raw_value))
        else:
            values = self.raw_value.split(',')
            return tuple(v.strip() for v in values)

    def _value_bool(self):
        if self.raw_value.lower() in ('true', 't', '1'):
            return True

        return False

    def _value_int(self):
        return int(self.raw_value)

    @property
    def value(self):
        if not self.active:
            return False

        if self.setting_type == self.DICT:
            return self._value_dict()
        elif self.setting_type == self.LIST:
            return self._value_list()
        elif self.setting_type == self.BOOL:
            return self._value_bool()
        elif self.setting_type == self.INT:
            return self._value_int()

        # Strings
        return self.raw_value
