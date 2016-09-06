import json
from mock import patch

from demotime import constants, models, tasks
from demotime.tests import BaseTestCase


class TestDTTasks(BaseTestCase):

    def setUp(self):
        super(TestDTTasks, self).setUp()
        req_patch = patch('demotime.tasks.requests.post')
        self.req_mock = req_patch.start()
        self.addCleanup(req_patch.stop)

    def test_fire_webhook(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        webhook = models.WebHook.create_webhook(
            project=review.project,
            target='http://www.example.org/',
            trigger_event=constants.CREATED
        )
        tasks.fire_webhook(review.pk, webhook.pk)
        self.req_mock.assert_called_once_with(
            webhook.target,
            data=json.dumps({
                'token': review.project.token,
                'webhook': webhook.to_json(),
                'review': review.to_json(),
            })
        )
