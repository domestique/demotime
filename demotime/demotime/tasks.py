from __future__ import absolute_import
import json
from socket import error as socket_error

import requests
from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail

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


@shared_task(bind=True)
def dt_send_mail(self, recipient, title, msg_text):
    if recipient.email:
        try:
            return send_mail(
                subject=title,
                message=msg_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=msg_text,
                fail_silently=True,
            )
        except socket_error:
            if settings.DT_PROD:
                self.retry()
    return 0
