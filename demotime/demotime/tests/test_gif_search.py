import json
from mock import Mock, patch
from requests.exceptions import HTTPError

from django.core.urlresolvers import reverse
from demotime.tests import BaseTestCase


class TestProfileViews(BaseTestCase):

    def setUp(self):
        super(TestProfileViews, self).setUp()
        assert self.client.login(
            username=self.user.username,
            password='testing'
        )
        self.requests_patch = patch('demotime.views.gif_search.requests')
        self.requests_mock = self.requests_patch.start()
        self.addCleanup(self.requests_patch.stop)

    def test_gif_search(self):
        resp_mock = Mock()
        resp_mock.status_code = 200
        resp_mock.content = bytearray(json.dumps({
            'meta': {'msg': 'OK', 'status': 200},
            'pagination': {'count': 25, 'offset': 0, 'total_count': 7766},
            'data': {
                'trending_datetime': '2016-07-14 16:08:32',
                'bitly_gif_url': 'http://gph.is/1LlM4Fd',
                'bitly_url': 'http://gph.is/1LlM4Fd',
                'url': 'https://giphy.com/gifs/reasons-key-peele-C9x0nrkuYlqjC',
                'source_tld': 'www.buzzfeed.com',
                'source_post_url': 'http://www.buzzfeed.com/ahmedaliakbar/reasons-you-should-be-obsessed-with-key-peele',
                'embed_url': 'https://giphy.com/embed/C9x0nrkuYlqjC',
                'username': '',
                'images': {
                    'fixed_height_small_still': {
                        'width': '180',
                        'url': 'https://media4.giphy.com/media/C9x0nrkuYlqjC/100_s.gif',
                        'height': '100'
                    },
                    'original': {
                        'width': '500',
                        'height': '278',
                        'mp4_size': '120260',
                        'frames': '25',
                        'webp_size': '627956',
                        'url': 'https://media4.giphy.com/media/C9x0nrkuYlqjC/giphy.gif',
                        'webp': 'https://media4.giphy.com/media/C9x0nrkuYlqjC/giphy.webp',
                        'size': '1815450',
                        'mp4': 'https://media4.giphy.com/media/C9x0nrkuYlqjC/giphy.mp4'
                    },
                },
                'type': 'gif',
                'content_url': '',
                'id': 'C9x0nrkuYlqjC',
                'import_datetime': '2015-09-10 09:46:01',
                'rating': 'g',
                'slug': 'reasons-key-peele-C9x0nrkuYlqjC',
                'is_indexable': 0,
                'source': 'http://www.buzzfeed.com/ahmedaliakbar/reasons-you-should-be-obsessed-with-key-peele'
            }
        }).encode('utf8'))
        self.requests_mock.get.return_value = resp_mock
        response = self.client.get(reverse('gif-search'), {'q': 'test'})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['error'], '')
        self.assertEqual(data['status'], 'success')
        gif_data = data['data']
        assert 'images' in gif_data
        assert 'fixed_height_small_still' in gif_data['images']
        self.assertEqual(gif_data['type'], 'gif')

    def test_gif_search_provider_unavailable(self):
        resp_mock = Mock()
        resp_mock.status_code = 500
        self.requests_mock.get.side_effect = [HTTPError('Fail!')]
        response = self.client.get(reverse('gif-search'), {'q': 'test'})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['error'], 'Failed to communicate with GIF service')
        self.assertEqual(data['status'], 'failed')

    def test_gif_search_bad_response(self):
        resp_mock = Mock()
        resp_mock.status_code = 500
        resp_mock.content = b'failure'
        self.requests_mock.get.return_value = resp_mock
        response = self.client.get(reverse('gif-search'), {'q': 'test'})
        self.assertStatusCode(response, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['error'], 'Bad response from GIF service')
        self.assertEqual(data['status'], 'failed')
