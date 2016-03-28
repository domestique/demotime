# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def update_photo_attachment_type(apps, schema_editor):
    Attachment = apps.get_model('demotime', 'Attachment')
    Attachment.objects.filter(
        attachment_type='photo',
    ).update(
        attachment_type='image',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0019_auto_20160327_1902'),
    ]

    operations = [
        migrations.RunPython(update_photo_attachment_type),
        migrations.AlterField(
            model_name='attachment',
            name='attachment_type',
            field=models.CharField(choices=[(b'', b'-----'), (b'image', b'Image'), (b'document', b'Document'), (b'movie', b'Movie/Screencast'), (b'audio', b'Audio'), (b'other', b'Other')], db_index=True, max_length=128),
        ),
    ]
