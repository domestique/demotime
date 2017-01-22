from django.core import mail
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
        creator, created = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        self.assertTrue(created)
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
        creator, _ = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        creator.active = False
        creator.save()

        creator, _ = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        self.assertTrue(creator.active)
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_create_creator_convert_reviewer(self):
        creator, created = models.Creator.create_creator(
            user=self.test_users[0], review=self.review, notify=False
        )
        self.assertTrue(creator.active)
        self.assertTrue(created)
        reviewer = self.review.reviewer_set.get(reviewer=self.test_users[0])
        self.assertFalse(reviewer.is_active)
        self.assertTrue(
            models.Event.objects.filter(
                user=reviewer.reviewer,
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).exists()
        )

    def test_create_creator_convert_reviewer_adding_user(self):
        creator, created = models.Creator.create_creator(
            user=self.test_users[0], review=self.review, notify=False,
            adding_user=self.user
        )
        self.assertTrue(creator.active)
        self.assertTrue(created)
        reviewer = self.review.reviewer_set.get(reviewer=self.test_users[0])
        self.assertFalse(reviewer.is_active)
        self.assertTrue(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.REVIEWER_REMOVED
            ).exists()
        )

    def test_create_creator_convert_follower(self):
        creator, created = models.Creator.create_creator(
            user=self.followers[0], review=self.review, notify=False
        )
        self.assertTrue(creator.active)
        self.assertTrue(created)
        follower = self.review.follower_set.get(user=self.followers[0])
        self.assertFalse(follower.is_active)
        self.assertTrue(
            models.Event.objects.filter(
                user=follower.user,
                event_type__code=models.EventType.FOLLOWER_REMOVED
            ).exists()
        )

    def test_create_creator_convert_follower_adding_user(self):
        creator, created = models.Creator.create_creator(
            user=self.followers[0], review=self.review, notify=False,
            adding_user=self.user
        )
        self.assertTrue(creator.active)
        self.assertTrue(created)
        follower = self.review.follower_set.get(user=self.followers[0])
        self.assertFalse(follower.is_active)
        self.assertTrue(
            models.Event.objects.filter(
                user=self.user,
                event_type__code=models.EventType.FOLLOWER_REMOVED
            ).exists()
        )

    def test_create_creator_notify_draft(self):
        self.review.state = constants.DRAFT
        self.review.save()
        models.Creator.create_creator(
            user=self.user, review=self.review,
            notify=True, adding_user=self.user
        )
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [self.user.email])
        self.assertEqual(
            msg.subject,
            '[DT-{}] - {}'.format(self.review.pk, self.review.title)
        )


    def test_create_creator_notify(self):
        mail.outbox = []
        creator, _ = models.Creator.create_creator(
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
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [self.user.email])
        self.assertEqual(
            msg.subject,
            '[DT-{}] - {}'.format(self.review.pk, self.review.title)
        )
        self.assertEqual(self.review.state, constants.PAUSED)

    def test_create_creator_event_added(self):
        creator, _ = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        # pylint: disable=protected-access
        event = creator._create_creator_event(self.user, removed=False)
        self.assertEqual(event.event_type.code, models.EventType.OWNER_ADDED)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_create_creator_event_removed(self):
        creator, _ = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        # pylint: disable=protected-access
        event = creator._create_creator_event(self.user, removed=True)
        self.assertEqual(event.event_type.code, models.EventType.OWNER_REMOVED)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.related_object, creator)

    def test_drop_creator(self):
        creator, _ = models.Creator.create_creator(
            user=self.user, review=self.review, notify=False
        )
        creator.drop_creator(self.co_owner)
        creator.refresh_from_db()

        self.assertFalse(creator.active)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [self.user.email])
        self.assertEqual(
            msg.subject,
            '[DT-{}] - {}'.format(self.review.pk, self.review.title)
        )
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
        _, created = models.Creator.create_creator(
            user=self.user, review=self.review, notify=True
        )
        self.assertFalse(created)
        self.assertFalse(models.Event.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_to_json(self):
        creator, _ = models.Creator.create_creator(
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
