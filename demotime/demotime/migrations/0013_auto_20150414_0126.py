# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0012_auto_20150412_2039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='display_name',
            field=models.CharField(max_length=2048, unique=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
