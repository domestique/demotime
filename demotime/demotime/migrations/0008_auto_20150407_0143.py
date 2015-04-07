# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0007_message_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created']},
        ),
        migrations.AlterModelOptions(
            name='commentthread',
            options={'ordering': ['-created'], 'get_latest_by': 'created'},
        ),
        migrations.AddField(
            model_name='message',
            name='deleted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attachment',
            name='attachment_type',
            field=models.CharField(db_index=True, max_length=128, choices=[(b'', b'-----'), (b'photo', b'Photo'), (b'document', b'Document'), (b'movie', b'Movie/Screencast'), (b'audio', b'Audio'), (b'other', b'Other')]),
            preserve_default=True,
        ),
    ]
