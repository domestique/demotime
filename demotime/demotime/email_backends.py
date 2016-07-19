import os

from hashlib import md5
from django.utils.text import slugify
from django.core.mail.backends.base import BaseEmailBackend

from django.conf import settings


class FileOutputEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        for message in email_messages:
            if not os.path.exists(settings.EMAIL_ROOT):
                os.mkdir(settings.EMAIL_ROOT)

            filename_slug = slugify('{}-{}-{}'.format(
                message.to,
                message.subject,
                md5(message.body.encode('utf-8')).hexdigest(),
            ))
            filename = '{}.html'.format(filename_slug)
            fh = open(os.path.join(settings.EMAIL_ROOT, filename), 'wb')
            fh.write(message.body.encode('utf-8'))
            fh.close()
