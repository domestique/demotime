import os
from hashlib import md5

from django.utils.text import slugify
from django.core.mail import EmailMessage
from django.test import TestCase, override_settings

from demotime.email_backends import FileOutputEmailBackend

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_PATH = os.path.join(CURRENT_PATH, 'test_data')


@override_settings(EMAIL_ROOT=TEST_DATA_PATH)
class TestFileOutputEmailBackend(TestCase):

    def test_file_written_for_email(self):
        message = EmailMessage(
            to=('test@example.com',),
            subject='Test Subject',
            body='This is a test email',
        )
        FileOutputEmailBackend().send_messages([message])
        filename = slugify('{}-{}-{}'.format(
            message.to,
            message.subject,
            md5(message.body.encode('utf-8')).hexdigest()
        ))
        expected_file = os.path.join(TEST_DATA_PATH, filename)
        self.assertTrue(os.path.exists(expected_file))
        self.assertEqual(
            open(expected_file).read(),
            message.body
        )
        os.remove(expected_file)
