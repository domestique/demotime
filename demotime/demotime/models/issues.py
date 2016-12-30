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

    def to_json(self):
        issue_dict = {
            'id': self.pk,
            'review_pk': self.review.pk,
            'review_title': self.review.title,
            'comment_pk': self.comment.pk,
            'created_by_name': self.created_by.userprofile.name,
            'created_by_pk': self.created_by.pk,
            'created_by_profile_url': self.created_by.userprofile.get_absolute_url(),
            'resolved_by_name': None,
            'resolved_by_pk': None,
            'resolved_by_profile_url': None,
        }
        if self.resolved_by:
            issue_dict.update({
                'resolved_by_name': self.resolved_by.userprofile.name,
                'resolved_by_pk': self.resolved_by.pk,
                'resolved_by_profile_url': self.resolved_by.userprofile.get_absolute_url()
            })

        return issue_dict

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
