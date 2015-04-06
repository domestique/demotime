# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_system_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.create(username='demotime_sys')


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0005_auto_20150404_2216'),
    ]

    operations = [
        migrations.RunPython(create_system_user)
    ]
