from __future__ import absolute_import
import re
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
    except: # pylint: disable=bare-except
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


def convert_dt_refs_to_links(text):
    matches = re.findall(r'DT-[\d]+', text, re.I)
    for match in matches:
        try:
            dt_pk = match.split('-')[1]
        except IndexError:
            return text
        else:
            if not models.Review.objects.filter(pk=dt_pk).exists():
                return text

        if not re.search('>{}<'.format(match), text):
            text = text.replace(
                match,
                '<a href="/{}/" target="_blank">{}</a>'.format(
                    match.upper(), match.upper()
                )
            )

    return text


@shared_task(bind=True)
def post_process_comment(self, comment_pk):
    try:
        comment = models.Comment.objects.get(pk=comment_pk)
    except models.Comment.DoesNotExist:
        self.retry()

    comment.comment = convert_dt_refs_to_links(comment.comment)
    comment.save(update_fields=['comment'])


@shared_task(bind=True)
def post_process_review(self, review_pk):
    try:
        review = models.Review.objects.get(pk=review_pk)
    except models.Review.DoesNotExist:
        self.retry()

    review.description = convert_dt_refs_to_links(review.description)
    review.save(update_fields=['description'])


@shared_task(bind=True)
def post_process_revision(self, revision_pk):
    try:
        revision = models.ReviewRevision.objects.get(pk=revision_pk)
    except models.ReviewRevision.DoesNotExist:
        self.retry()

    revision.description = convert_dt_refs_to_links(revision.description)
    revision.save(update_fields=['description'])
