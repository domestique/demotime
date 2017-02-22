from django.core.exceptions import ObjectDoesNotExist, ValidationError

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReactionModels(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.comment = models.Comment.create_comment(
            commenter=self.user,
            review=self.review.revision,
            comment='Test Comment',
            attachments=[],
        )
        self.event = models.Event.objects.first()
        self.attachment = models.Attachment.objects.first()

    def test_create_reaction_type(self):
        reaction_type = models.ReactionType.create_reaction_type(
            'Test Reaction Type', 'test-reaction-type'
        )
        self.assertEqual(reaction_type.name, 'Test Reaction Type')
        self.assertEqual(reaction_type.code, 'test-reaction-type')
        self.assertEqual(
            reaction_type.__str__(),
            'ReactionType: Test Reaction Type - test-reaction-type'
        )
        self.assertEqual(reaction_type.to_json(), {
            'pk': reaction_type.pk,
            'name': 'Test Reaction Type',
            'code': 'test-reaction-type'
        })

    def test_create_reaction_revision(self):
        reaction = models.Reaction.create_reaction(
            project=self.project, review=self.review,
            revision=self.review.revision,
            user=self.user, reaction_type=constants.LOVE,
        )
        reaction_type = models.ReactionType.objects.get(code=constants.LOVE)
        self.assertEqual(reaction.project, self.project)
        self.assertEqual(reaction.review, self.review)
        self.assertEqual(reaction.revision, self.review.revision)
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.reaction_type, reaction_type)
        self.assertIsNone(reaction.comment)
        self.assertIsNone(reaction.attachment)
        self.assertIsNone(reaction.event)
        self.assertEqual(
            reaction.__str__(),
            'Reaction: {}, Love, {}'.format(self.user, self.review)
        )
        self.assertEqual(reaction.to_json(), {
            'pk': reaction.pk,
            'project': self.project.pk,
            'review': self.review.pk,
            'reaction_type': reaction.reaction_type.to_json(),
            'attachment': None,
            'revision': self.review.to_json(),
            'comment': None,
            'event': None,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'created': reaction.created.isoformat(),
            'modified': reaction.modified.isoformat(),
        })

    def test_create_reaction_event(self):
        reaction = models.Reaction.create_reaction(
            project=self.project, review=self.review,
            event=self.event, user=self.user, reaction_type=constants.LOVE,
        )
        reaction_type = models.ReactionType.objects.get(code=constants.LOVE)
        self.assertEqual(reaction.project, self.project)
        self.assertEqual(reaction.review, self.review)
        self.assertEqual(reaction.event, self.event)
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.reaction_type, reaction_type)
        self.assertIsNone(reaction.comment)
        self.assertIsNone(reaction.attachment)
        self.assertIsNone(reaction.revision)
        self.assertEqual(reaction.to_json(), {
            'pk': reaction.pk,
            'project': self.project.pk,
            'review': self.review.pk,
            'reaction_type': reaction.reaction_type.to_json(),
            'attachment': None,
            'revision': None,
            'comment': None,
            'event': self.event.to_json(),
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'created': reaction.created.isoformat(),
            'modified': reaction.modified.isoformat(),
        })

    def test_create_reaction_attachment(self):
        reaction = models.Reaction.create_reaction(
            project=self.project, review=self.review,
            attachment=self.attachment, user=self.user,
            reaction_type=constants.LOVE
        )
        reaction_type = models.ReactionType.objects.get(code=constants.LOVE)
        self.assertEqual(reaction.project, self.project)
        self.assertEqual(reaction.review, self.review)
        self.assertEqual(reaction.attachment, self.attachment)
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.reaction_type, reaction_type)
        self.assertIsNone(reaction.comment)
        self.assertIsNone(reaction.revision)
        self.assertIsNone(reaction.event)
        self.assertEqual(reaction.to_json(), {
            'pk': reaction.pk,
            'project': self.project.pk,
            'review': self.review.pk,
            'reaction_type': reaction.reaction_type.to_json(),
            'attachment': self.attachment.to_json(),
            'revision': None,
            'comment': None,
            'event': None,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'created': reaction.created.isoformat(),
            'modified': reaction.modified.isoformat(),
        })

    def test_create_reaction_comment(self):
        reaction = models.Reaction.create_reaction(
            project=self.project, review=self.review,
            comment=self.comment, user=self.user,
            reaction_type=constants.LOVE
        )
        reaction_type = models.ReactionType.objects.get(code=constants.LOVE)
        self.assertEqual(reaction.project, self.project)
        self.assertEqual(reaction.review, self.review)
        self.assertEqual(reaction.comment, self.comment)
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.reaction_type, reaction_type)
        self.assertIsNone(reaction.attachment)
        self.assertIsNone(reaction.revision)
        self.assertIsNone(reaction.event)
        self.assertEqual(reaction.to_json(), {
            'pk': reaction.pk,
            'project': self.project.pk,
            'review': self.review.pk,
            'reaction_type': reaction.reaction_type.to_json(),
            'attachment': None,
            'revision': None,
            'comment': self.comment.to_json(),
            'event': None,
            'user_pk': self.user.pk,
            'user_profile_url': self.user.userprofile.get_absolute_url(),
            'created': reaction.created.isoformat(),
            'modified': reaction.modified.isoformat(),
        })

    def test_create_reaction_multiple_objects(self):
        with self.assertRaises(ValidationError) as exc:
            models.Reaction.create_reaction(
                project=self.project, review=self.review,
                comment=self.comment, revision=self.review.revision,
                user=self.user, reaction_type=constants.LOVE
            )

        self.assertEqual(
            exc.exception.message,
            "Can't react to multiple objects in one reaction"
        )

    def test_creation_reaction_no_objects(self):
        with self.assertRaises(ValidationError) as exc:
            models.Reaction.create_reaction(
                project=self.project, review=self.review,
                user=self.user, reaction_type=constants.LOVE,
            )

        self.assertEqual(
            exc.exception.message,
            "create_reaction requires 1 attachment, comment, event or revision"
        )

    def test_creation_reaction_invalid_reaction_type(self):
        with self.assertRaises(ObjectDoesNotExist):
            models.Reaction.create_reaction(
                project=self.project, review=self.review,
                comment=self.comment, user=self.user,
                reaction_type='THIS IS NOT REAL'
            )
