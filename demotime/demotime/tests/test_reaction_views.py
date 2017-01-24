import json

from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestReactionViews(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.url = reverse('reactions', kwargs={'proj_slug': self.project.slug})
        self.reaction = models.Reaction.create_reaction(
            project=self.project, review=self.review,
            revision=self.review.revision,
            user=self.user, reaction_type=constants.LOVE,
        )
        self.second_review = models.Review.create_review(**self.default_review_kwargs)
        self.second_reaction = models.Reaction.create_reaction(
            project=self.project, review=self.second_review,
            revision=self.second_review.revision,
            user=self.user, reaction_type=constants.LOVE,
        )
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )

    def test_requires_authentication(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertStatusCode(response, 302) # Redirect to Login

    def test_get_reactions(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        reactions = models.Reaction.objects.all()
        reaction_json = [reaction.to_json() for reaction in reactions]
        self.assertEqual(data, {
            'errors': {},
            'status': 'success',
            'reactions': reaction_json
        })
        self.assertEqual(len(data['reactions']), 2)

    def test_get_reactions_for_review(self):
        response = self.client.get(self.url, data={'review': self.review.pk})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf-8'))
        reactions = models.Reaction.objects.filter(review=self.review)
        reaction_json = [reaction.to_json() for reaction in reactions]
        self.assertEqual(data, {
            'errors': {},
            'status': 'success',
            'reactions': reaction_json
        })
        self.assertEqual(len(data['reactions']), 1)

    def test_create_reaction(self):
        self.assertEqual(models.Reaction.objects.count(), 2)
        response = self.client.post(self.url, data={
            'review': self.review.pk,
            'user': self.user.pk,
            'reaction_type': constants.PLUS_ONE,
            'object_type': 'revision',
            'object_pk': self.review.revision.pk,
        })
        self.assertStatusCode(response, 201)
        self.assertEqual(models.Reaction.objects.count(), 3)
        reaction = models.Reaction.objects.get(
            reaction_type__code=constants.PLUS_ONE)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'status': 'success',
            'errors': {},
            'reaction': reaction.to_json(),
        })

    def test_create_reaction_invalid_pk(self):
        self.assertEqual(models.Reaction.objects.count(), 2)
        response = self.client.post(self.url, data={
            'review': self.review.pk,
            'user': self.user.pk,
            'reaction_type': constants.PLUS_ONE,
            'object_type': 'revision',
            'object_pk': 184761,
        })
        self.assertStatusCode(response, 400)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'status': 'failure',
            'errors': {'object_pk': ['Invalid PK supplied']},
            'reaction': {},
        })

    def test_delete_reaction(self):
        url = reverse('reactions', kwargs={
            'proj_slug': self.project.slug,
            'reaction_pk': self.reaction.pk,
        })
        response = self.client.delete(url)
        self.assertStatusCode(response, 200)
        self.assertFalse(
            models.Reaction.objects.filter(pk=self.reaction.pk).exists()
        )
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'status': 'success',
            'errors': {},
            'reaction': None,
        })

    def test_delete_reaction_not_owned(self):
        self.client.logout()
        test_user_1 = self.test_users[0]
        self.client.login(username=test_user_1.username, password='testing')
        url = reverse('reactions', kwargs={
            'proj_slug': self.project.slug,
            'reaction_pk': self.reaction.pk,
        })
        response = self.client.delete(url)
        self.assertStatusCode(response, 400)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data, {
            'status': 'failure',
            'errors': {'user': "User can not delete reaction they don't own."},
            'reaction': self.reaction.to_json()
        })
        self.assertTrue(
            models.Reaction.objects.filter(pk=self.reaction.pk).exists()
        )
