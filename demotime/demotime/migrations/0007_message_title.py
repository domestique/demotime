# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0006_auto_20150404_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='title',
            field=models.CharField(default='a', max_length=1024),
            preserve_default=False,
        ),
    ]
