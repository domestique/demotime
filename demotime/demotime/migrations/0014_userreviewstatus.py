# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def create_user_review_statuses(apps, schema_editor):
    UserReviewStatus = apps.get_model('demotime', 'UserReviewStatus')
    Review = apps.get_model('demotime', 'Review')
    for review in Review.objects.all():
        UserReviewStatus.objects.create(
            review=review,
            user=review.creator,
            read=False
        )
        for reviewer in review.reviewer_set.all():
            UserReviewStatus.objects.create(
                review=review,
                user=reviewer.reviewer,
                read=False
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demotime', '0013_auto_20150414_0126'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserReviewStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('read', models.BooleanField(default=False)),
                ('review', models.ForeignKey(to='demotime.Review')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(create_user_review_statuses),
    ]
