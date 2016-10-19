import json
from mock import patch

from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.views import events
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

    def test_filter_events_by_review(self):
        response = self.client.get(self.url, {'review': self.review_one.pk})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        expected_events = models.Event.objects.filter(
            review=self.review_one
        )
        self.assertTrue(expected_events.exists())
        self.assertEqual(
            len(data['events']),
            expected_events.count()
        )

    def test_filter_events_by_event_type(self):
        response = self.client.get(self.url, {
            'event_type': models.EventType.DEMO_CREATED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        expected_events = models.Event.objects.filter(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertTrue(expected_events.exists())
        self.assertEqual(
            len(data['events']),
            expected_events.count()
        )

    def test_exclude_events(self):
        response = self.client.get(self.url, {
            'exclude_type': models.EventType.DEMO_CREATED
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        expected_events = models.Event.objects.exclude(
            event_type__code=models.EventType.DEMO_CREATED
        )
        self.assertTrue(expected_events.exists())
        self.assertEqual(
            len(data['events']),
            expected_events.count()
        )

    def test_filter_events_by_multiple_event_types(self):
        models.Comment.create_comment(
            self.user, 'comment', self.review_one.revision
        )
        response = self.client.get(self.url, {
            'event_type': [
                models.EventType.DEMO_CREATED, models.EventType.COMMENT_ADDED
            ]
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        expected_events = models.Event.objects.filter(
            event_type__code__in=(
                models.EventType.COMMENT_ADDED, models.EventType.DEMO_CREATED
            )
        )
        self.assertEqual(expected_events.count(), 3)
        self.assertEqual(len(data['events']), expected_events.count())
        for event in data['events']:
            self.assertIn(
                event['event_type']['code'],
                (models.EventType.COMMENT_ADDED, models.EventType.DEMO_CREATED)
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
        expected_events = models.Event.objects.filter(
            event_type__code=models.EventType.DEMO_CREATED,
            review=self.review_one
        )
        self.assertTrue(expected_events.exists())
        self.assertEqual(
            len(data['events']),
            expected_events.count()
        )

    def test_no_draft_or_cancelled_events(self):
        self.default_review_kwargs['state'] = constants.DRAFT
        review = models.Review.create_review(**self.default_review_kwargs)
        response = self.client.get(self.url, {
            'review': review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 0)

        self.default_review_kwargs['state'] = constants.CANCELLED
        self.default_review_kwargs['review'] = review.pk
        review = models.Review.update_review(**self.default_review_kwargs)
        response = self.client.get(self.url, {
            'review': review.pk
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 0)

    @patch.object(events.EventView, 'paginate_by', new=2)
    def test_events_view_pagination(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 2)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_count'], 6)
        self.assertEqual(data['count'], models.Event.objects.all().count())

        # Page 2
        response = self.client.get(self.url, {
            'page': 2
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 2)
        self.assertEqual(data['page'], '2')
        self.assertEqual(data['page_count'], 6)
        self.assertEqual(data['count'], models.Event.objects.all().count())

    @patch.object(events.EventView, 'paginate_by', new=2)
    def test_events_view_not_an_int_page(self):
        response = self.client.get(self.url, {
            'page': 'words'
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 2)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_count'], 6)

    @patch.object(events.EventView, 'paginate_by', new=2)
    def test_events_view_invalid_page(self):
        response = self.client.get(self.url, {
            'page': 2000
        })
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['errors'], '')
        self.assertEqual(len(data['events']), 2)
        self.assertEqual(data['page'], 6)
        self.assertEqual(data['page_count'], 6)
