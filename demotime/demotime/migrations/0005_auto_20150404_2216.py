# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demotime', '0004_auto_20150329_1740'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentThread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('review_revision', models.ForeignKey(to='demotime.ReviewRevision')),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('message', models.TextField(blank=True)),
                ('read', models.BooleanField(default=False)),
                ('receipient', models.ForeignKey(related_name='receipient', to=settings.AUTH_USER_MODEL)),
                ('review', models.ForeignKey(to='demotime.ReviewRevision', null=True)),
                ('sender', models.ForeignKey(related_name='sender', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(to='demotime.CommentThread', null=True)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='reviewrevision',
            options={'ordering': ['-created'], 'get_latest_by': 'created'},
        ),
        migrations.RemoveField(
            model_name='comment',
            name='review',
        ),
        migrations.AddField(
            model_name='comment',
            name='thread',
            field=models.ForeignKey(default=1, to='demotime.CommentThread'),
            preserve_default=False,
        ),
    ]
