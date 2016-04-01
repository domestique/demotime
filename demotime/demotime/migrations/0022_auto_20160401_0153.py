# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-01 01:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0021_messagebundle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='bundle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demotime.MessageBundle'),
        ),
        migrations.AlterUniqueTogether(
            name='messagebundle',
            unique_together=set([('review', 'owner')]),
        ),
    ]
