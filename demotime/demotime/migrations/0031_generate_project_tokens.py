# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-01 20:42
from __future__ import unicode_literals

from uuid import uuid4

from django.db import migrations


def generate_project_tokens(apps, schema_editor):
    Project = apps.get_model('demotime', 'Project')

    for project in Project.objects.all():
        project.token = uuid4().hex
        project.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0030_auto_20160701_1539'),
    ]

    operations = [
        migrations.RunPython(generate_project_tokens)
    ]