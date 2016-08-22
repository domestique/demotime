# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-13 18:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0033_auto_20160717_1651'),
    ]

    operations = [
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=128)),
                ('key', models.SlugField(max_length=128)),
                ('description', models.TextField(blank=True)),
                ('raw_value', models.TextField()),
                ('setting_type', models.CharField(choices=[('list', 'List'), ('bool', 'Boolean'), ('dict', 'Dictionary'), ('string', 'String'), ('int', 'Integer')], db_index=True, max_length=32)),
                ('active', models.BooleanField(default=False)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='demotime.Project')),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
    ]
