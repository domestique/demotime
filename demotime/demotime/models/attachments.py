import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .base import BaseModel


def attachment_filename(instance, filename):
    ''' method for determing the path of uploads '''
    if hasattr(instance.content_object, 'review'):
        folder = instance.content_object.review.pk
    else:
        folder = instance.content_object.pk
    folder = str(folder)
    return os.path.join('reviews', folder, filename)


class Attachment(BaseModel):

    IMAGE = 'image'
    DOCUMENT = 'document'
    MOVIE = 'movie'
    AUDIO = 'audio'
    OTHER = 'other'

    ATTACHMENT_TYPE_CHOICES = (
        ('', '-----'),
        (IMAGE, 'Image'),
        (DOCUMENT, 'Document'),
        (MOVIE, 'Movie/Screencast'),
        (AUDIO, 'Audio'),
        (OTHER, 'Other'),
    )

    attachment = models.FileField(upload_to=attachment_filename)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    attachment_type = models.CharField(
        max_length=128,
        choices=ATTACHMENT_TYPE_CHOICES,
        db_index=True,
    )
    description = models.CharField(max_length=2048, blank=True, null=True)

    @property
    def pretty_name(self):
        ''' Just cleaning up the filename display a bit '''
        return ''.join(self.attachment.name.split('/')[1:])

    class Meta:
        index_together = [
            ('content_type', 'object_id'),
        ]
        app_label = 'demotime'
        get_latest_by = 'created'
