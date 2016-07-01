from django.db import models

from demotime import constants
from demotime.models.base import BaseModel


class WebHook(BaseModel):

    HOOK_TRIGGERS = (
        (constants.CREATED, 'Demo Created'),
        (constants.CLOSED, 'Demo Closed'),
        (constants.ABORTED, 'Demo Aborted'),
        (constants.COMMENT, 'Comment Added'),
        (constants.UPDATED, 'Demo Updated'),
    )

    project = models.ForeignKey('Project')
    target = models.CharField(max_length=1024)
    trigger_event = models.CharField(
        max_length=64, choices=HOOK_TRIGGERS, db_index=True
    )

    def _to_json(self):
        return {
            'project_pk': self.project.pk,
            'pk': self.pk,
            'target': self.target,
            'trigger_event': self.trigger_event
        }

    @classmethod
    def create_webhook(cls, project, target, trigger_event):
        obj = cls.objects.create(
            project=project,
            target=target,
            trigger_event=trigger_event
        )
        return obj
