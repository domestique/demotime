# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='creator',
            field=models.ForeignKey(related_name='creator', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
