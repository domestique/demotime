from socket import error as socket_error

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.core.mail import send_mail

from .base import BaseModel


class MessageBundle(BaseModel):

    review = models.ForeignKey('Review', null=True)
    owner = models.ForeignKey('auth.User')
    read = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-modified']

    def get_absolute_url(self):
        return reverse('message-detail', args=[self.pk])

    @property
    def title(self):
        if self.review:
            return self.review.title
        else:
            return self.message_set.get().title

    @classmethod
    def create_message_bundle(cls, owner, review=None):
        if review:
            bundle, _ = cls.objects.get_or_create(
                review=review,
                owner=owner
            )
        else:
            bundle = cls.objects.create(
                review=review,
                owner=owner
            )

        bundle.read = False
        bundle.deleted = False
        bundle.save(update_fields=['read', 'deleted'])
        return bundle


class Message(BaseModel):

    receipient = models.ForeignKey('auth.User', related_name='receipient')
    sender = models.ForeignKey('auth.User', related_name='sender')
    title = models.CharField(max_length=1024)
    review = models.ForeignKey('ReviewRevision', null=True)
    thread = models.ForeignKey('CommentThread', null=True)
    message = models.TextField(blank=True)
    bundle = models.ForeignKey('MessageBundle')

    def __unicode__(self):
        return u'Message for {}, From {}'.format(
            self.receipient.username, self.sender.username
        )

    def _send_email(self, recipient, title, msg_text):
        if recipient.email:
            try:
                return send_mail(
                    title,
                    msg_text,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    html_message=msg_text,
                    fail_silently=True,
                )
            except socket_error:
                if settings.DT_PROD:
                    raise

        return 0

    @classmethod
    def send_system_message(
            cls, title, template_name, context_dict, receipient,
            revision=None, thread=None, email=True
    ):
        system_user = User.objects.get(username='demotime_sys')
        context_dict.update({
            'sender': system_user,
            'dt_url': settings.SERVER_URL,
        })
        msg_text = loader.get_template(
            template_name
        ).render(Context(context_dict))
        obj = cls.create_message(
            receipient=receipient,
            sender=system_user,
            title=title,
            review_revision=revision,
            message=msg_text,
            thread=thread,
            email=email,
        )
        return obj

    @classmethod
    def create_message(
            cls, receipient, sender, title,
            review_revision, thread, message, email=True,
    ):
        bundle = MessageBundle.create_message_bundle(
            review=review_revision.review if review_revision else None,
            owner=receipient,
        )
        obj = cls.objects.create(
            receipient=receipient,
            sender=sender,
            title=title,
            review=review_revision,
            thread=thread,
            message=message,
            bundle=bundle,
        )
        if email:
            obj._send_email(receipient, title, message)
        return obj

    class Meta:
        ordering = ['-created']
