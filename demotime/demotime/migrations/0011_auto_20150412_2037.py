# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import demotime.models.users


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demotime', '0010_auto_20150410_0026'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('avatar', models.ImageField(null=True, upload_to=demotime.models.users.avatar_field, blank=True)),
                ('bio', models.TextField()),
                ('display_name', models.CharField(max_length=2048, null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='review',
            name='state',
            field=models.CharField(default=b'open', max_length=128, db_index=True, choices=[(b'open', b'Open'), (b'closed', b'Closed'), (b'aborted', b'Aborted')]),
            preserve_default=True,
        ),
    ]
