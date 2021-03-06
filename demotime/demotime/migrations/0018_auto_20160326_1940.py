# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-26 19:40
from __future__ import unicode_literals

from django.db import migrations, models


def backfill_revision_numbers(apps, schema_editor):
    Review = apps.get_model('demotime', 'Review')

    for review in Review.objects.all():
        for count, rev in enumerate(review.reviewrevision_set.all().order_by('created'), start=1):
            rev.number = count
            rev.save(update_fields=['number'])

class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0017_auto_20160326_1724'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewrevision',
            name='number',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='case_link',
            field=models.CharField(blank=True, max_length=2048, verbose_name=b'Case URL'),
        ),
        migrations.RunPython(backfill_revision_numbers)
    ]
