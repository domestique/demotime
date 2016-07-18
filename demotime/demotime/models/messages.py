from socket import error as socket_error

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template import loader
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

        needs_save = False
        if bundle.read:
            bundle.read = False
            needs_save = True

        if bundle.deleted:
            bundle.deleted = False
            needs_save = True

        if needs_save:
            bundle.save(update_fields=['read', 'deleted', 'modified'])

        return bundle


class Message(BaseModel):

    receipient = models.ForeignKey('auth.User', related_name='receipient')
    sender = models.ForeignKey('auth.User', related_name='sender')
    title = models.CharField(max_length=1024)
    review = models.ForeignKey('ReviewRevision', null=True)
    thread = models.ForeignKey('CommentThread', null=True)
    message = models.TextField(blank=True)
    bundle = models.ForeignKey('MessageBundle')

    def __str__(self):
        return 'Message for {}, From {}'.format(
            self.receipient.username, self.sender.username
        )

    def _send_email(self, recipient, title, msg_text):
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
                    raise

        return 0

    @classmethod
    def _render_message_text(self, context_dict, template_name, email=False):
        context_dict['is_email'] = email
        return loader.get_template(template_name).render(context_dict)

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
        msg_text = cls._render_message_text(context_dict, template_name)
        email_text = cls._render_message_text(context_dict, template_name, True)
        obj = cls.create_message(
            receipient=receipient,
            sender=system_user,
            title=title,
            review_revision=revision,
            message=msg_text,
            thread=thread,
            email=email,
            email_text=email_text,
        )
        return obj

    @classmethod
    def create_message(
            cls, receipient, sender, title,
            review_revision, thread, message, email=True,
            email_text='',
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
            subject = title
            if review_revision:
                subject = '[DT-{}] - {}'.format(
                    review_revision.review.pk,
                    review_revision.review.title
                )
            obj._send_email(receipient, subject, email_text)
        return obj

    class Meta:
        ordering = ['-created']
