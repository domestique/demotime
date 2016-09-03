from __future__ import absolute_import
import json

import requests
from celery import shared_task

from demotime import models


@shared_task(bind=True)
def fire_webhook(self, review_pk, webhook_pk, additional_json=None):
    webhook = models.WebHook.objects.get(pk=webhook_pk)
    review = models.Review.objects.get(pk=review_pk)
    json_data = {
        'token': review.project.token,
        'webhook': webhook.to_json(),
        'review': review.to_json(),
    }
    if additional_json:
        json_data.update(additional_json)

    try:
        requests.post(webhook.target, data=json.dumps(json_data))
    except:
        self.retry()
