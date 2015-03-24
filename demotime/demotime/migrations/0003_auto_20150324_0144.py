# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0002_auto_20150323_0228'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='reviewer',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='reviewrevision',
            options={'get_latest_by': 'created'},
        ),
        migrations.AddField(
            model_name='attachment',
            name='attachment_type',
            field=models.CharField(default='photo', max_length=128, db_index=True, choices=[(b'photo', b'Photo'), (b'document', b'Document'), (b'movie', b'Movie/Screencast'), (b'audio', b'Audio'), (b'other', b'Other')]),
            preserve_default=False,
        ),
    ]
