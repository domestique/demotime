# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-24 22:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0028_create_projects_groups_group_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demotime.Project'),
        ),
    ]