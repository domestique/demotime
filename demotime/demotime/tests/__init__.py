from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import BytesIO, File


class BaseTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.user.set_password('testing')
        self.user.email = 'test_user@example.com'
        self.user.save()
        self.system_user = User.objects.get(username='demotime_sys')
        for x in range(0, 3):
            u = User.objects.create_user(username='test_user_{}'.format(x))
            u.set_password('testing')
            u.email = '{}@example.com'.format(u.username)
            u.save()

        self.test_users = User.objects.filter(username__startswith="test_user_")
        self.default_review_kwargs = {
            'creator': self.user,
            'title': 'Test Title',
            'description': 'Test Description',
            'case_link': 'http://example.org/',
            'reviewers': self.test_users,
            'attachments': [
                {
                    'attachment': File(BytesIO('test_file_1')),
                    'attachment_type': 'image',
                    'description': 'Testing',
                },
                {
                    'attachment': File(BytesIO('test_file_2')),
                    'attachment_type': 'image',
                    'description': 'Testing',
                },
            ],
        }

    def assertStatusCode(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
