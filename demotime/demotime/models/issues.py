from django.db import models
from django.core.exceptions import ValidationError

from demotime.models.base import BaseModel
from demotime.models import Event, EventType


class Issue(BaseModel):

    review = models.ForeignKey('Review')
    comment = models.ForeignKey('Comment')
    created_by = models.ForeignKey(
        'auth.User', related_name='issue_creator'
    )
    resolved_by = models.ForeignKey(
        'auth.User', null=True, related_name='issue_resolver'
    )

    def __str__(self):
        return 'Issue {} on DT-{}, Created by: {}'.format(
            self.pk, self.review.pk, self.created_by.username
        )

    def create_issue_event(self, resolved_by=None):
        if resolved_by:
            event = Event.create_event(
                self.review.project,
                EventType.ISSUE_RESOLVED,
                self,
                resolved_by
            )
        else:
            event = Event.create_event(
                self.review.project,
                EventType.ISSUE_CREATED,
                self,
                self.created_by
            )

        return event

    @classmethod
    def create_issue(cls, review, comment, created_by):
        existing_issues = cls.objects.filter(
            review=review, comment=comment, resolved_by__isnull=True
        ).exists()
        if existing_issues:
            raise ValidationError(
                'Issue already exists for DT-{}, Comment PK: {}'.format(
                    review.pk, comment.pk
                )
            )

        obj = cls.objects.create(
            review=review,
            comment=comment,
            created_by=created_by
        )
        obj.create_issue_event()
        return obj

    def resolve(self, resolved_by):
        self.resolved_by = resolved_by
        self.save(update_fields=['modified', 'resolved_by'])
        self.create_issue_event(resolved_by)

    @property
    def is_resolved(self):
        return True if self.resolved_by else False

    class Meta(object):
        index_together = (
            ('review', 'comment'),
            ('review', 'comment', 'resolved_by')
        )
