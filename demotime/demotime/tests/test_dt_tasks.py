import json
from mock import patch

from demotime import constants, models, tasks
from demotime.tests import BaseTestCase


class TestDTTasks(BaseTestCase):

    def setUp(self):
        super(TestDTTasks, self).setUp()
        req_patch = patch('demotime.tasks.requests.post')
        self.req_mock = req_patch.start()
        self.addCleanup(req_patch.stop)

    def test_fire_webhook(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        webhook = models.WebHook.create_webhook(
            project=review.project,
            target='http://www.example.org/',
            trigger_event=constants.CREATED
        )
        tasks.fire_webhook(review.pk, webhook.pk)
        self.req_mock.assert_called_once_with(
            webhook.target,
            data=json.dumps({
                'token': review.project.token,
                'webhook': webhook.to_json(),
                'review': review.to_json(),
            })
        )

    def test_convert_dt_refs_to_links_successful_match(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        text = tasks.convert_dt_refs_to_links('link to dt-{}'.format(review.pk))
        self.assertEqual(
            text,
            'link to <a href="/DT-{}/" target="_blank">DT-{}</a>'.format(
                review.pk, review.pk
            )
        )

    def test_convert_dt_refs_to_links_uppercase(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        text = tasks.convert_dt_refs_to_links('link to DT-{}'.format(review.pk))
        self.assertEqual(
            text,
            'link to <a href="/DT-{}/" target="_blank">DT-{}</a>'.format(
                review.pk, review.pk
            )
        )

    def test_convert_dt_refs_to_links_ignore_bad_links(self):
        text = tasks.convert_dt_refs_to_links('link to dt-1231241')
        self.assertEqual(text, 'link to dt-1231241')

    def test_convert_dt_refs_to_links_no_duped_links(self):
        text = tasks.convert_dt_refs_to_links(
            'link to <a href="">dt-1231241</a>'
        )
        self.assertEqual(text, 'link to <a href="">dt-1231241</a>')

    def test_post_process_comment(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        second_review = models.Review.create_review(**self.default_review_kwargs)
        comment = models.Comment.create_comment(
            commenter=self.user,
            review=review.revision,
            comment='Link me to DT-{}'.format(second_review.pk),
            attachments=[],
        )
        comment.refresh_from_db()
        self.assertEqual(
            comment.comment,
            'Link me to <a href="/DT-{}/" target="_blank">DT-{}</a>'.format(
                second_review.pk, second_review.pk
            )
        )

    def test_post_process_review(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        self.default_review_kwargs['description'] = 'Link to DT-{}'.format(
            review.pk
        )
        second_review = models.Review.create_review(**self.default_review_kwargs)
        second_review.refresh_from_db()
        self.assertEqual(
            second_review.description,
            'Link to <a href="/DT-{}/" target="_blank">DT-{}</a>'.format(
                review.pk, review.pk
            )
        )

    def test_post_process_revision(self):
        review = models.Review.create_review(**self.default_review_kwargs)
        second_review = models.Review.create_review(**self.default_review_kwargs)
        self.default_review_kwargs['review'] = second_review.pk
        self.default_review_kwargs['description'] = 'Link to DT-{}'.format(review.pk)
        models.Review.update_review(**self.default_review_kwargs)
        second_rev = second_review.revision
        self.assertEqual(
            second_rev.description,
            'Link to <a href="/DT-{}/" target="_blank">DT-{}</a>'.format(
                review.pk, review.pk
            )
        )
