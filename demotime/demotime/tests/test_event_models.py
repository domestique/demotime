from demotime import models
from demotime.tests import BaseTestCase


class TestEventModels(BaseTestCase):

    def setUp(self):
        super(TestEventModels, self).setUp()

    def test_create_event_type(self):
        event_type = models.EventType.create_event_type(
            name='Test Event Type',
            code='test-event-type',
        )
        self.assertEqual(event_type.name, 'Test Event Type')
        self.assertEqual(event_type.code, 'test-event-type')
        self.assertEqual(event_type.__str__(), 'EventType: Test Event Type')

    def test_event_type_to_json(self):
        event_type = models.EventType.create_event_type(
            name='Test Event Type',
            code='test-event-type',
        )
        self.assertEqual(event_type.to_json(), {
            'id': event_type.pk,
            'name': event_type.name,
            'code': event_type.code,
        })

    def test_event_creation(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        event = models.Event.create_event(
            review.project,
            models.EventType.DEMO_CREATED,
            review,
            review.creator
        )
        self.assertEqual(event.event_type.code, models.EventType.DEMO_CREATED)
        self.assertEqual(event.related_type, models.Event.REVIEW)
        self.assertEqual(event.user, review.creator)
        self.assertEqual(event.related_object, review)
        self.assertEqual(event.__str__(), 'Event {} on {}'.format(
            event.event_type.name, event.related_object
        ))

    def test_event_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        event = models.Event.create_event(
            review.project,
            models.EventType.DEMO_CREATED,
            review,
            review.creator
        )
        self.assertEqual(event.to_json(), {
            'project': {
                'id': review.project.pk,
                'name': review.project.name,
                'slug': review.project.slug,
            },
            'event_type': event.event_type.to_json(),
            'related_type': event.REVIEW,
            'related_type_pretty': 'Review',
            'related_object': review.to_json(),
        })
