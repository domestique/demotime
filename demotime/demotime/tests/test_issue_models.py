from django.core.exceptions import ValidationError

from demotime import models
from demotime.tests import BaseTestCase


class TestIssueModels(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.review = models.Review.create_review(**self.default_review_kwargs)
        self.comment = models.Comment.create_comment(
            self.user, 'test comment', self.review.revision,
        )
        self.test_user = self.test_users[0]

    def test_create_issue(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        self.assertEqual(issue.review, self.review)
        self.assertEqual(issue.comment, self.comment)
        self.assertEqual(issue.created_by, self.test_user)
        self.assertIsNone(issue.resolved_by)
        self.assertFalse(issue.is_resolved)
        self.assertEqual(
            issue.__str__(),
            'Issue {} on DT-{}, Created by: {}'.format(
                issue.pk, issue.review.pk, issue.created_by.username
            )
        )
        events = models.Event.objects.filter(
            event_type__code=models.EventType.ISSUE_CREATED
        )
        self.assertEqual(events.count(), 1)
        event = events.get()
        self.assertEqual(event.user, self.test_user)
        self.assertEqual(event.review, issue.review)
        self.assertEqual(event.project, issue.review.project)
        self.assertEqual(event.related_object, issue)
        self.assertEqual(self.review.open_issue_count, 1)
        self.assertEqual(self.review.resolved_issue_count, 0)

    def test_create_dupe_issue(self):
        models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        with self.assertRaises(ValidationError) as exc:
            models.Issue.create_issue(
                self.review, self.comment, self.test_user
            )

        self.assertEqual(
            exc.exception.message,
            'Issue already exists for DT-{}, Comment PK: {}'.format(
                self.review.pk, self.comment.pk
            )
        )

    def test_issue_to_json(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        self.assertEqual(issue.to_json(), {
            'id': issue.pk,
            'review_pk': issue.review.pk,
            'review_title': issue.review.title,
            'comment_pk': issue.comment.pk,
            'created_by_name': issue.created_by.userprofile.name,
            'created_by_pk': issue.created_by.pk,
            'created_by_profile_url': issue.created_by.userprofile.get_absolute_url(),
            'resolved_by_name': None,
            'resolved_by_pk': None,
            'resolved_by_profile_url': None,
        })

    def test_resolved_issue_to_json(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        issue.resolve(self.user)
        self.assertEqual(issue.to_json(), {
            'id': issue.pk,
            'review_pk': issue.review.pk,
            'review_title': issue.review.title,
            'comment_pk': issue.comment.pk,
            'created_by_name': issue.created_by.userprofile.name,
            'created_by_pk': issue.created_by.pk,
            'created_by_profile_url': issue.created_by.userprofile.get_absolute_url(),
            'resolved_by_name': issue.resolved_by.userprofile.name,
            'resolved_by_pk': issue.resolved_by.pk,
            'resolved_by_profile_url': issue.resolved_by.userprofile.get_absolute_url()
        })

    def test_resolve_issue(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        issue.resolve(self.user)
        self.assertEqual(issue.resolved_by, self.user)
        self.assertTrue(issue.is_resolved)
        events = models.Event.objects.filter(
            event_type__code=models.EventType.ISSUE_RESOLVED
        )
        self.assertEqual(events.count(), 1)
        event = events.get()
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.review, issue.review)
        self.assertEqual(event.project, issue.review.project)
        self.assertEqual(event.related_object, issue)
        self.assertEqual(self.review.open_issue_count, 0)
        self.assertEqual(self.review.resolved_issue_count, 1)

    def test_resolved_manager_method(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        self.assertFalse(models.Issue.objects.resolved().exists())
        self.assertFalse(self.review.issue_set.resolved().exists())
        issue.resolved_by = self.user
        issue.save(update_fields=['resolved_by'])
        self.assertTrue(models.Issue.objects.resolved().exists())
        self.assertTrue(self.review.issue_set.resolved().exists())

    def test_open_manager_method(self):
        issue = models.Issue.create_issue(
            self.review, self.comment, self.test_user
        )
        self.assertTrue(models.Issue.objects.open().exists())
        self.assertTrue(self.review.issue_set.open().exists())
        issue.resolved_by = self.user
        issue.save(update_fields=['resolved_by'])
        self.assertFalse(models.Issue.objects.open().exists())
        self.assertFalse(self.review.issue_set.open().exists())
