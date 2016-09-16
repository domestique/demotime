

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template import loader
from django.core.urlresolvers import reverse


from demotime.models.base import BaseModel
from demotime.tasks import dt_send_mail


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

    # pylint: disable=no-self-use
    def _send_email(self, recipient, title, msg_text):
        dt_send_mail.delay(
            recipient, title, msg_text
        )

    @classmethod
    def _render_message_text(cls, context_dict, template_name, email=False):
        context_dict['is_email'] = email
        return loader.get_template(template_name).render(context_dict)

    # pylint: disable=too-many-arguments
    @classmethod
    def send_system_message(
            cls, title, template_name, context_dict, receipient,
            revision=None, thread=None, email=True
    ):
        system_user = User.objects.get(username='demotime_sys')
        context_dict.update({
            'sender': system_user,
            'dt_url': settings.SERVER_URL,
            'dt_prod': settings.DT_PROD,
        })
        msg_text = cls._render_message_text(context_dict, template_name)
        obj = cls.create_message(
            receipient=receipient,
            sender=system_user,
            title=title,
            review_revision=revision,
            message=msg_text,
            thread=thread,
        )
        if email:
            context_dict['bundle'] = obj.bundle
            email_text = cls._render_message_text(
                context_dict, template_name, True
            )
            subject = title
            if revision:
                subject = '[DT-{}] - {}'.format(
                    revision.review.pk,
                    revision.review.title
                )
            # pylint: disable=protected-access
            obj._send_email(receipient, subject, email_text)
        return obj

    @classmethod
    def create_message(
            cls, receipient, sender, title,
            review_revision, thread, message
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
        return obj

    class Meta:
        ordering = ['-created']
