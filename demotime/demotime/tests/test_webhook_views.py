from django.core.urlresolvers import reverse

from demotime import constants, models
from demotime.tests import BaseTestCase


class TestWebHookViews(BaseTestCase):

    def setUp(self):
        super(TestWebHookViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.project_url = reverse('project-detail', args=[self.project.slug])

    def test_create_web_hook(self):
        url = reverse('webhook-create', args=[self.project.slug])
        response = self.client.post(url, {
            'trigger_event': constants.REOPENED,
            'target': 'http://example.org/test-create-web-hook',
        })
        self.assertStatusCode(response, 302)
        self.assertRedirects(response, self.project_url)
        hook = models.WebHook.objects.get(
            target='http://example.org/test-create-web-hook'
        )
        self.assertEqual(hook.trigger_event, constants.REOPENED)

    def test_create_web_hook_errors(self):
        url = reverse('webhook-create', args=[self.project.slug])
        response = self.client.post(url, {
            'trigger_event': 'bad_event',
            'target': 'http://example.org/test-create-web-hook-errors/',
        })
        self.assertStatusCode(response, 200)
        self.assertFormError(
            response,
            'form',
            'trigger_event',
            'Select a valid choice. bad_event is not one of the available choices.'
        )
        self.assertFalse(
            models.WebHook.objects.filter(
                target='http://example.org/test-create-web-hook-errors/'
            ).exists()
        )

    def test_edit_web_hook(self):
        hook = models.WebHook.create_webhook(
            self.project,
            constants.COMMENT,
            'http://example.org/test-edit-web-hook',
        )
        url = reverse('webhook-edit', args=[self.project.slug, hook.pk])
        response = self.client.post(url, {
            'trigger_event': constants.REOPENED,
            'target': 'http://example.org/test-edit-web-hook-edited/'
        })
        self.assertStatusCode(response, 302)
        self.assertRedirects(response, self.project_url)
        edited_hook = models.WebHook.objects.get(
            target='http://example.org/test-edit-web-hook-edited/'
        )
        self.assertEqual(edited_hook.trigger_event, constants.REOPENED)
        self.assertEqual(hook.pk, edited_hook.pk)

    def test_delete_web_hook(self):
        hook = models.WebHook.create_webhook(
            self.project,
            constants.COMMENT,
            'http://example.org/test-delete-web-hook',
        )
        url = reverse('webhook-edit', args=[self.project.slug, hook.pk])
        response = self.client.post(url, {
            'trigger_event': constants.COMMENT,
            'target': 'http://example.org/test-delete-web-hook/',
            'delete': True,
        })
        self.assertStatusCode(response, 302)
        self.assertRedirects(response, self.project_url)
        self.assertFalse(
            models.WebHook.objects.filter(pk=hook.pk).exists()
        )
