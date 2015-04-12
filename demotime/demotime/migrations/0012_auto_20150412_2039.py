# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_user_profiles(apps, schema_editor):
    UserProfile = apps.get_model('demotime', 'UserProfile')
    User = apps.get_model('auth', 'User')
    for user in User.objects.all():
        UserProfile.objects.create(user=user)

class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0011_auto_20150412_2037'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles),
    ]
