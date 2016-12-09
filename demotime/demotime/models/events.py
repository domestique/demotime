from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from demotime.models.base import BaseModel


class EventType(BaseModel):

    DEMO_CREATED = 'demo-created'
    DEMO_OPENED = 'demo-opened'
    DEMO_CLOSED = 'demo-closed'
    DEMO_ABORTED = 'demo-aborted'
    DEMO_UPDATED = 'demo-updated'
    DEMO_APPROVED = 'demo-approved'
    DEMO_REJECTED = 'demo-rejected'
    DEMO_REVIEWING = 'demo-reviewing'
    DEMO_PAUSED = 'demo-paused'
    COMMENT_ADDED = 'comment-added'
    REVIEWER_APPROVED = 'reviewer-approved'
    REVIEWER_REJECTED = 'reviewer-rejected'
    REVIEWER_RESET = 'reviewer-reset'
    REVIEWER_ADDED = 'reviewer-added'
    REVIEWER_REMOVED = 'reviewer-removed'
    FOLLOWER_ADDED = 'follower-added'
    FOLLOWER_REMOVED = 'follower-removed'
    OWNER_ADDED = 'owner-added'
    OWNER_REMOVED = 'owner-removed'

    name = models.CharField(max_length=128)
    code = models.SlugField(unique=True)

    def __str__(self):
        return 'EventType: {}'.format(self.name)

    @classmethod
    def create_event_type(cls, name, code):
        return cls.objects.create(
            name=name,
            code=code
        )

    def to_json(self):
        return {
            'id': self.pk,
            'name': self.name,
            'code': self.code,
        }


class Event(BaseModel):

    COMMENT = 'comment'
    FOLLOWER = 'follower'
    REVIEW = 'review'
    REVIEWER = 'reviewer'
    REVISION = 'revision'
    CREATOR = 'creator'

    RELATED_TYPES = [
        COMMENT, FOLLOWER, REVIEW, REVIEWER, REVISION, CREATOR
    ]

    RELATED_TYPE_CHOICES = (
        (COMMENT, 'Comment'),
        (FOLLOWER, 'Follower'),
        (REVIEW, 'Review'),
        (REVIEWER, 'Reviewer'),
        (REVISION, 'Revision'),
        (CREATOR, 'Creator')
    )

    project = models.ForeignKey('Project')
    review = models.ForeignKey('Review')
    event_type = models.ForeignKey('EventType')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')
    related_type = models.CharField(max_length=64, choices=RELATED_TYPE_CHOICES)
    user = models.ForeignKey('auth.User')

    def __str__(self):
        return 'Event {} on {}'.format(self.event_type.name, self.related_object)

    @classmethod
    def _get_review(cls, related_object, related_type):
        if related_type == cls.REVIEW:
            return related_object
        elif related_type == cls.COMMENT:
            return related_object.thread.review_revision.review
        elif related_type == cls.FOLLOWER:
            return related_object.review
        elif related_type == cls.REVIEWER:
            return related_object.review
        elif related_type == cls.CREATOR:
            return related_object.review
        elif related_type == cls.REVISION:
            return related_object.review
        else:
            raise RuntimeError('Invalid related_type')

    @classmethod
    def create_event(cls, project, event_type_code, related_object, user):
        event_type = EventType.objects.get(code=event_type_code)
        related_type = related_object._meta.model_name  # pylint: disable=protected-access
        if related_type not in cls.RELATED_TYPES:
            raise RuntimeError('Invalid related object passed to Event creation')

        return cls.objects.create(
            project=project,
            event_type=event_type,
            related_object=related_object,
            related_type=related_type,
            user=user,
            review=cls._get_review(related_object, related_type)
        )

    def to_json(self):
        return {
            'project': {
                'id': self.project.pk,
                'slug': self.project.slug,
                'name': self.project.name,
            },
            'review': self.review.to_json(),
            'event_type': self.event_type.to_json(),
            'related_type': self.related_type,
            'related_type_pretty': self.get_related_type_display(),
            'related_object': self.related_object.to_json(),
            'user': {
                'name': self.user.userprofile.name,
                'username': self.user.username,
                'pk': self.user.pk,
                'url': self.user.userprofile.get_absolute_url(),
            },
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    class Meta:
        index_together = [
            ('content_type', 'object_id'),
        ]
        get_latest_by = 'created'
        ordering = ('-created',)
