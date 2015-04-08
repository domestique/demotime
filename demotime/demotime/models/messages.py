from django.db import models
from django.core.urlresolvers import reverse

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

    @classmethod
    def create_message(cls, receipient, sender, title, review_revision, thread, message):
        return cls.objects.create(
            receipient=receipient,
            sender=sender,
            title=title,
            review=review_revision,
            thread=thread,
            message=message,
        )

    class Meta:
        ordering = ['-created']
