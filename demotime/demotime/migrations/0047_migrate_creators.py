# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-12-03 22:06
from __future__ import unicode_literals

from django.db import migrations


def migrate_creators(apps, _):
    Review = apps.get_model('demotime', 'Review')
    Creator = apps.get_model('demotime', 'Creator')
    for review in Review.objects.all():
        Creator.objects.create(
            user=review.creator,
            active=True,
            review=review,
        )
        review.last_action_by = review.creator
        review.save(update_fields=['last_action_by'])

def create_owner_event_types(apps, _):
    EventType = apps.get_model('demotime', 'EventType')
    EventType.objects.create(
        name='Owner Added',
        code='owner-added'
    )
    EventType.objects.create(
        name='Owner Removed',
        code='owner-removed'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0046_auto_20161203_1605'),
    ]

    operations = [
        migrations.RunPython(migrate_creators),
        migrations.RunPython(create_owner_event_types)
    ]