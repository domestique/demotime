# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-02 15:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_message_bundles(apps, schema_editor):
    Message = apps.get_model('demotime', 'Message')
    MessageBundle = apps.get_model('demotime', 'MessageBundle')
    User = apps.get_model('auth', 'User')

    for user in User.objects.all():
        for msg in user.receipient.all():
            if msg.bundle:
                continue

            if not msg.review:
                bundle = MessageBundle.objects.create(
                    review=None,
                    owner=msg.receipient,
                )
                msg.bundle = bundle
                msg.save(update_fields=['bundle'])
            else:
                bundle, _ = MessageBundle.objects.get_or_create(
                    review=msg.review.review, # its really a ReviewRevision
                    owner=msg.receipient,
                )
                Message.objects.filter(
                    review=msg.review,
                    receipient=msg.receipient,
                ).update(bundle=bundle)

            if all(read for read in bundle.message_set.values_list('read', flat=True)):
                bundle.read = True

            if all(deleted for deleted in bundle.message_set.values_list('deleted', flat=True)):
                bundle.deleted = True

            bundle.save(update_fields=['read', 'deleted'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demotime', '0021_messagebundle'),
    ]

    operations = [
        migrations.RunPython(create_message_bundles),
    ]
