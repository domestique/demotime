from mock import Mock

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
            review.creator_set.active().get().user
        )
        self.assertEqual(event.event_type.code, models.EventType.DEMO_CREATED)
        self.assertEqual(event.related_type, models.Event.REVIEW)
        self.assertEqual(event.user, review.creator)
        self.assertEqual(event.related_object, review)
        self.assertEqual(event.__str__(), 'Event {} on {}'.format(
            event.event_type.name, event.related_object
        ))
        self.assertEqual(event.review, review)

    def test_get_review_review(self):
        obj = Mock()
        # pylint: disable=protected-access
        res = models.Event._get_review(obj, models.Event.REVIEW)
        self.assertEqual(res, obj)

    def test_get_review_comment(self):
        obj = Mock()
        # pylint: disable=protected-access
        res = models.Event._get_review(obj, models.Event.COMMENT)
        self.assertEqual(res, obj.thread.review_revision.review)

    def test_get_review_follower(self):
        obj = Mock()
        # pylint: disable=protected-access
        res = models.Event._get_review(obj, models.Event.FOLLOWER)
        self.assertEqual(res, obj.review)

    def test_get_review_reviewer(self):
        obj = Mock()
        # pylint: disable=protected-access
        res = models.Event._get_review(obj, models.Event.REVIEWER)
        self.assertEqual(res, obj.review)

    def test_get_review_revision(self):
        obj = Mock()
        # pylint: disable=protected-access
        res = models.Event._get_review(obj, models.Event.REVISION)
        self.assertEqual(res, obj.review)

    def test_get_review_runtimeerror(self):
        obj = Mock()
        with self.assertRaises(RuntimeError):
            # pylint: disable=protected-access
            models.Event._get_review(obj, 'not real')

    def test_event_to_json(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        event = models.Event.create_event(
            review.project,
            models.EventType.DEMO_CREATED,
            review,
            review.creator_set.active().get().user
        )
        self.assertEqual(event.to_json(), {
            'project': {
                'id': review.project.pk,
                'name': review.project.name,
                'slug': review.project.slug,
            },
            'review': review.to_json(),
            'event_type': event.event_type.to_json(),
            'related_type': event.REVIEW,
            'related_type_pretty': 'Review',
            'related_object': review.to_json(),
            'created': event.created.isoformat(),
            'modified': event.modified.isoformat(),
            'user': {
                'name': event.user.userprofile.name,
                'username': event.user.username,
                'pk': event.user.pk,
                'url': event.user.userprofile.get_absolute_url(),
            },
        })
