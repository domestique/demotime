# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-23 22:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0036_auto_20160813_1448'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={'get_latest_by': 'created', 'ordering': ('sort_order',)},
        ),
        migrations.AddField(
            model_name='attachment',
            name='sort_order',
            field=models.IntegerField(default=1),
        ),
    ]
