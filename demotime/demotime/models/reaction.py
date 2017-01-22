from django.db import models
from django.core.exceptions import ValidationError

from demotime.models.base import BaseModel


class ReactionType(BaseModel):

    name = models.CharField(max_length=64)
    code = models.SlugField(unique=True)

    def __str__(self):
        return 'ReactionType: {} - {}'.format(
            self.name, self.code
        )

    def to_json(self):
        return {
            'pk': self.pk,
            'name': self.name,
            'code': self.code,
        }

    @classmethod
    def create_reaction_type(cls, name, code):
        return cls.objects.create(
            name=name, code=code
        )


class Reaction(BaseModel):

    reaction_type = models.ForeignKey('ReactionType')
    project = models.ForeignKey('Project')
    review = models.ForeignKey('Review')
    attachment = models.ForeignKey('Attachment', null=True)
    revision = models.ForeignKey('ReviewRevision', null=True)
    comment = models.ForeignKey('Comment', null=True)
    event = models.ForeignKey('Event', null=True)
    user = models.ForeignKey('auth.User')

    def __str__(self):
        return 'Reaction: {}, {}, {}'.format(
            self.user, self.reaction_type.name, self.review
        )

    def to_json(self):
        return {
            'pk': self.pk,
            'project': self.project.pk,
            'review': self.review.pk,
            'reaction_type': self.reaction_type.to_json(),
            'attachment': self.attachment.to_json() if self.attachment else None,
            'revision': self.revision.review.to_json() if self.revision else None,
            'comment': self.comment.to_json() if self.comment else None,
            'event': self.event.to_json() if self.event else None,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    @classmethod
    def create_reaction(
            cls, project, review, user, reaction_type,
            attachment=None, revision=None, comment=None, event=None
    ):
        react_objs = [attachment, revision, comment, event]
        empty_react_objs = [item for item in react_objs if item is None]
        if len(empty_react_objs) == len(react_objs):
            raise ValidationError(
                "create_reaction requires 1 attachment, comment, event or revision"
            )

        if len(empty_react_objs) < len(react_objs) - 1:
            raise ValidationError(
                "Can't react to multiple objects in one reaction"
            )

        reaction_type = ReactionType.objects.get(code=reaction_type)
        return cls.objects.create(
            reaction_type=reaction_type,
            project=project,
            review=review,
            user=user,
            attachment=attachment,
            revision=revision,
            comment=comment,
            event=event,
        )
