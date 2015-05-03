# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demotime', '0015_userprofile_user_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('reminder_type', models.CharField(db_index=True, max_length=256, choices=[(b'creator', b'Creator'), (b'reviewer', b'Reviewer')])),
                ('remind_at', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('review', models.ForeignKey(to='demotime.Review')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reminder',
            unique_together=set([('review', 'user')]),
        ),
        migrations.AlterModelOptions(
            name='attachment',
            options={'get_latest_by': 'created'},
        ),
    ]
