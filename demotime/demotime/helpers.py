from django.contrib.auth.models import User
from django.template import loader
from django.conf import settings

from html.parser import HTMLParser

from demotime.tasks import dt_send_mail


class MLStripper(HTMLParser):

    def __init__(self):
        super(MLStripper, self).__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def send_system_message(
        subject, template_name, context_dict, recipient,
        revision=None
):
    system_user = User.objects.get(username='demotime_sys')
    context_dict.update({
        'sender': system_user,
        'dt_url': settings.SERVER_URL,
        'dt_prod': settings.DT_PROD,
        'site_settings': settings,
    })
    email_text = loader.get_template(template_name).render(context_dict)
    if revision:
        subject = '[DT-{}] - {}'.format(
            revision.review.pk,
            revision.review.title
        )
    dt_send_mail.delay(recipient, subject, email_text)
