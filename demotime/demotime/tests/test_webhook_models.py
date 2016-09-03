from demotime import constants, models
from demotime.tests import BaseTestCase


class TestWebHookModels(BaseTestCase):

    def test_create_webhook(self):
        hook = models.WebHook.create_webhook(
            self.project,
            'http://www.example.org/',
            constants.CREATED
        )
        self.assertEqual(hook.project, self.project)
        self.assertEqual(hook.target, 'http://www.example.org/')
        self.assertEqual(hook.trigger_event, constants.CREATED)

    def test_to_json(self):
        hook = models.WebHook.create_webhook(
            self.project,
            'http://www.example.org/',
            constants.CREATED
        )
        self.assertEqual(hook.to_json(), {
            'project_pk': hook.project.pk,
            'pk': hook.pk,
            'target': hook.target,
            'trigger_event': hook.trigger_event
        })
