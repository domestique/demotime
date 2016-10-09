import json

from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestEventViews(BaseTestCase):

    def setUp(self):
        super(TestEventViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.review_one = models.Review.create_review(
            **self.default_review_kwargs
        )
        second_review_kwargs = self.default_review_kwargs.copy()
        second_review_kwargs['title'] = 'Second Demo'
        self.review_two = models.Review.create_review(
            **second_review_kwargs
        )
        self.url = reverse(
            'events', kwargs={'proj_slug': self.project.slug}
        )

    def test_get_events(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(
            len(data['events']),
            self.project.event_set.count()
        )

    def test_get_events_hides_drafts(self):
        models.Review.objects.update(state=constants.DRAFT)
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(
            len(data['events']), 0
        )

    def test_filter_events_by_review(self):
        response = self.client.get(self.url, {'review': self.review_one.pk})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(
            len(data['events']),
            models.Event.objects.filter(
                review=self.review_one
            ).count()
        )

    def test_filter_events_by_event_type(self):
        response = self.client.get(self.url, {
            'event_type': models.EventType.DEMO_CREATED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(
            len(data['events']),
            models.Event.objects.filter(
                event_type__code=models.EventType.DEMO_CREATED
            ).count()
        )

    def test_filter_events_by_type_and_review(self):
        response = self.client.get(self.url, {
            'event_type': models.EventType.DEMO_CREATED,
            'review': self.review_one.pk,
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(
            len(data['events']),
            models.Event.objects.filter(
                event_type__code=models.EventType.DEMO_CREATED,
                review=self.review_one
            ).count()
        )
