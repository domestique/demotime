# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-13 18:35
from __future__ import unicode_literals

from django.db import migrations

SETTINGS = {
    'emojis_enabled': {
        'title': 'Emojis Enabled',
        'raw_value': 'true',
        'setting_type': 'bool',
        'description': 'When enabled, users will be able to add emojis to their Demos',
        'active': True,
    },
    'reminder_days': {
        'title': 'Reminder Days',
        'raw_value': '2',
        'setting_type': 'int',
        'description': 'Number of days before a Reminder is sent',
        'active': True,
    },
    'gifs_enabled': {
        'title': 'Gif Embedding Enabled',
        'raw_value': 'true',
        'setting_type': 'bool',
        'description': 'When enabled, users will be able to embed gifs from Giphy',
        'active': True,
    }
}


def create_settings(apps, schema_editor):
    Project = apps.get_model('demotime', 'Project')
    Setting = apps.get_model('demotime', 'Setting')
    projects = Project.objects.all()

    for key, values in SETTINGS.items():
        Setting.objects.create(
            title=values['title'],
            raw_value=values['raw_value'],
            description=values['description'],
            setting_type=values['setting_type'],
            active=values['active'],
            key=key,
        )

    for project in projects:
        for setting in Setting.objects.all():
            setting.pk = None
            setting.project = project
            setting.save()


def revert_settings(apps, schema_editor):
    Setting = apps.get_model('demotime', 'Setting')
    Setting.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0034_setting'),
    ]

    operations = [
        migrations.RunPython(create_settings, revert_settings),
    ]
