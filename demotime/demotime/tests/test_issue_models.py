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
