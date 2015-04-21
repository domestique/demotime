# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def update_demotime_sys_profile(apps, schema_editor):
    UserProfile = apps.get_model('demotime', 'UserProfile')
    User = apps.get_model('auth', 'User')
    user = User.objects.get(username='demotime_sys')
    profile = UserProfile.objects.get(user=user)
    profile.user_type = 'system'
    profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0014_userreviewstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(default=b'user', max_length=1024, choices=[(b'user', b'User'), (b'system', b'System')]),
            preserve_default=True,
        ),
        migrations.RunPython(update_demotime_sys_profile),
    ]
