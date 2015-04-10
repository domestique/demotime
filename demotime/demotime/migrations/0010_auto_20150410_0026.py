# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demotime', '0009_attachment_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='reviewer_state',
            field=models.CharField(default=b'reviewing', max_length=128, db_index=True, choices=[(b'reviewing', b'Reviewing'), (b'approved', b'Approved'), (b'rejected', b'Rejected')]),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='review',
            old_name='status',
            new_name='state',
        ),
        migrations.AlterField(
            model_name='reviewer',
            name='status',
            field=models.CharField(default=b'reviewing', max_length=128, db_index=True, choices=[(b'reviewing', b'Reviewing'), (b'rejected', b'Rejected'), (b'approved', b'Approved')]),
            preserve_default=True,
        ),
    ]
