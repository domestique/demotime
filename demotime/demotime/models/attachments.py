import os

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from demotime import constants
from demotime.models.base import BaseModel


def attachment_filename(instance, filename):
    ''' method for determing the path of uploads '''
    if hasattr(instance.content_object, 'review'):
        folder = instance.content_object.review.pk
    else:
        folder = instance.content_object.pk
    folder = str(folder)
    return os.path.join('reviews', folder, filename)

def determine_attachment_type(filename):
    try:
        suffix = filename.split('.')[-1]
    except AttributeError:
        suffix = 'unknown_format'

    for attachment_type, suffixes in constants.ATTACHMENT_MAP.items():
        if suffix.lower() in suffixes:
            return attachment_type

    return constants.OTHER


class Attachment(BaseModel):

    ATTACHMENT_TYPE_CHOICES = (
        ('', '-----'),
        (constants.IMAGE, 'Image'),
        (constants.DOCUMENT, 'Document'),
        (constants.MOVIE, 'Movie/Screencast'),
        (constants.AUDIO, 'Audio'),
        (constants.OTHER, 'Other'),
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
    sort_order = models.IntegerField(default=1)

    def to_json(self):
        return {
            'pk': self.pk,
            'static_url': reverse('user-media', args=[self.pk]),
            'attachment_type': self.attachment_type,
            'description': self.description,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    @classmethod
    def create_attachment(cls, attachment, content_object,
                          description='', sort_order=0):
        obj = cls.objects.create(
            attachment=attachment,
            content_object=content_object,
            attachment_type=determine_attachment_type(attachment.name),
            sort_order=sort_order,
            description=description,
        )
        return obj

    @property
    def pretty_name(self):
        ''' Just cleaning up the filename display a bit '''
        return ''.join(self.attachment.name.split('/')[-1])

    @property
    def review(self):
        from demotime import models
        if isinstance(self.content_object, models.Comment):
            return self.content_object.thread.review_revision.review

        elif isinstance(self.content_object, models.Review):
            return self.content_object

        elif isinstance(self.content_object, models.ReviewRevision):
            return self.content_object.review

    @property
    def project(self):
        return self.review.project

    class Meta:
        index_together = [
            ('content_type', 'object_id'),
        ]
        app_label = 'demotime'
        get_latest_by = 'created'
        ordering = ('sort_order',)
