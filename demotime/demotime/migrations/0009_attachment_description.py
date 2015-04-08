# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0008_auto_20150407_0143'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='description',
            field=models.CharField(max_length=2048, null=True, blank=True),
            preserve_default=True,
        ),
    ]
