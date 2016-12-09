from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.core import mail

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestCreatorModels(BaseTestCase):

    def setUp(self):
        super(TestCreatorModels, self).setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        # Purge creators and events
        self.review.creator_set.all().delete()
        models.Event.objects.all().delete()
        mail.outbox = []

    def test_create_creator_no_notify(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        self.assertEqual(creator.user, self.user)
        self.assertEqual(creator.review, self.review)
        self.assertTrue(creator.active)
        self.assertEqual(
            creator.__str__(),
            'Creator: {} - {}'.format(
                self.user.userprofile.name, self.review.title
            )
        )
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_create_creator_no_notify_inactive(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        creator.active = False
        creator.save()

        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        self.assertTrue(creator.active)
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_create_creator_notify_draft(self):
        self.review.state = constants.DRAFT
        self.review.save()
        creator = models.Creator.create_creator(
            user=self.user, review=self.review,
            notify=True, adding_user=self.user
        )
        event = models.Event.objects.get()
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.user, self.user
        )
        self.assertEqual(
            event.related_object, creator
        )
        self.assertEqual(len(mail.outbox), 1)
        message = models.Message.objects.get(
            title='You have been added as an owner of {}'.format(self.review.title)
        )
        self.assertEqual(message.receipient, self.user)

    def test_create_creator_notify(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review,
            notify=True, adding_user=self.user
        )
        event = models.Event.objects.exclude(
            event_type__code=models.EventType.DEMO_PAUSED
        ).get()
        self.assertEqual(
            event.event_type.code, models.EventType.OWNER_ADDED
        )
        self.assertEqual(
            event.user, self.user
        )
        self.assertEqual(
            event.related_object, creator
        )
        self.assertEqual(len(mail.outbox), 6)
        message = models.Message.objects.get(
            title='You have been added as an owner of {}'.format(self.review.title)
        )
        self.assertEqual(message.receipient, self.user)
        self.assertEqual(self.review.state, constants.PAUSED)

    def test_create_creator_event_added(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        # pylint: disable=protected-access
        event = creator._create_creator_event(self.user, removed=False)
        self.assertEqual(event.event_type.code, models.EventType.OWNER_ADDED)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_create_creator_event_removed(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        # pylint: disable=protected-access
        event = creator._create_creator_event(self.user, removed=True)
        self.assertEqual(event.event_type.code, models.EventType.OWNER_REMOVED)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_drop_creator(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        creator.drop_creator(self.co_owner)
        creator.refresh_from_db()

        self.assertFalse(creator.active)
        self.assertEqual(len(mail.outbox), 1)
        message = models.Message.objects.get(
            title='You have been removed as an owner of {}'.format(
                self.review.title
            )
        )
        self.assertEqual(message.receipient, self.user)
        event = models.Event.objects.get()
        self.assertEqual(event.event_type.code, models.EventType.OWNER_REMOVED)
        self.assertEqual(event.user, self.co_owner)
        self.assertEqual(event.related_object, creator)

    def test_create_too_many_creators(self):
        creators = [self.user, self.co_owner]
        extra_user = User.objects.create_user(username='extra')
        for creator in creators:
            models.Creator.create_creator(
                user=creator, review=self.review, notify=False
            )

        with self.assertRaises(ValidationError) as exc:
            models.Creator.create_creator(
                user=extra_user, review=self.review, notify=False
            )

        self.assertEqual(
            exc.exception.message,
            'Demos may have a maximum of 2 Owners'
        )

    def test_create_dupe_creators(self):
        models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        # Now we do it again, but we'll set notify to True and prove nothing
        # ends up happening
        models.Creator.create_creator(
            user=self.user, review=self.review, notify=True
        )
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_to_json(self):
        creator = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        self.assertEqual(creator.to_json(), {
            'name': creator.user.userprofile.name,
            'user_pk': creator.user.pk,
            'user_profile_url': creator.user.userprofile.get_absolute_url(),
            'creator_pk': creator.pk,
            'review_pk': creator.review.pk,
            'created': creator.created.isoformat(),
            'modified': creator.modified.isoformat()
        })
