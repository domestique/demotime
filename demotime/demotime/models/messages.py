from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.core.mail import send_mail

from .base import BaseModel


class Message(BaseModel):

    receipient = models.ForeignKey('auth.User', related_name='receipient')
    sender = models.ForeignKey('auth.User', related_name='sender')
    title = models.CharField(max_length=1024)
    review = models.ForeignKey('ReviewRevision', null=True)
    thread = models.ForeignKey('CommentThread', null=True)
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Message for {}, From {}'.format(
            self.receipient.username, self.sender.username
        )

    def get_absolute_url(self):
        return reverse('message-detail', args=[self.pk])

    def _send_email(self, recipient, title, msg_text):
        if recipient.email:
            return send_mail(
                title,
                msg_text,
                settings.DEFAULT_FROM_EMAIL,
                [recipient.email],
                fail_silently=True,
            )

        return 0

    @classmethod
    def send_system_message(
            cls, title, template_name, context_dict, receipient,
            revision=None, thread=None, email=True
    ):
        system_user = User.objects.get(username='demotime_sys')
        context_dict['sender'] = system_user
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
        )
        return obj

    @classmethod
    def create_message(
            cls, receipient, sender, title,
            review_revision, thread, message, email=True,
    ):
        obj = cls.objects.create(
            receipient=receipient,
            sender=sender,
            title=title,
            review=review_revision,
            thread=thread,
            message=message,
        )
        if email:
            obj._send_email(receipient, title, message)
        return obj

    class Meta:
        ordering = ['-created']
