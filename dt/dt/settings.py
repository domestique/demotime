"""
Django settings for dt project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from configparser import ConfigParser

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
parser = ConfigParser()
parser.read('/etc/demotime/demotime.ini')
if not parser.has_section('demotime'):
    parser.add_section('demotime')
    parser.set('demotime', 'server_url', 'demoti.me')
    parser.set('demotime', 'default_from_email', 'demos@demoti.me')
    parser.set('demotime', 'email_backend', 'django.core.mail.backends.console.EmailBackend')
    parser.set('demotime', 'timezone', 'America/Chicago')
    parser.set('demotime', 'default_reminder_days', '2')
    parser.set('demotime', 'dt_prod', 'false')
    if os.environ.get('TRAVIS', '').lower() == 'true':
        parser.set('demotime', 'static_root', os.path.join(BASE_DIR, 'static'))
        parser.set('demotime', 'media_root', os.path.join(BASE_DIR, 'uploads'))
    else:
        parser.set('demotime', 'static_root', '/usr/local/demotime/static')
        parser.set('demotime', 'media_root', '/usr/local/demotime/uploads')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'zf3o4tx%22pzoauflj+z2=$l2@g&$656!7d5ir)hdj4g!mv8$%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Our libs
    'demotime',
    # Third Party Libs
    'macros',
    'registration'
)

try:
    import django_nose
except ImportError:
    pass
else:
    INSTALLED_APPS += ('django_nose', )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'dt.urls'

WSGI_APPLICATION = 'dt.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'demotime_docker',
        'HOST': 'db',
        'PORT': 5432,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = parser.get('demotime', 'timezone')

USE_I18N = True

USE_L10N = True

USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.core.context_processors.debug',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.static',
                'django.core.context_processors.tz',
                'django.core.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'demotime.context_processors.has_unread_messages',
                'demotime.context_processors.unread_message_count',
                'demotime.context_processors.site_settings',
                'demotime.context_processors.available_projects',
            ],
        },
    },
]

# MEDIA SETTINGS
STATIC_URL = '/static/'
MEDIA_URL = '/protected/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
STATIC_ROOT = parser.get('demotime', 'static_root')
MEDIA_ROOT = parser.get('demotime', 'media_root')

# TEST SETTINGS
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--logging-filter=-django.db.backends.schema',
    '--with-id',
]

# MAIL_SETTINGS
DEFAULT_FROM_EMAIL = parser.get('demotime', 'default_from_email')
EMAIL_BACKEND = parser.get('demotime', 'email_backend')

# ACCOUNT SETTINGS
LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
AUTHENTICATION_BACKENDS = ['demotime.authentication_backends.UserProxyModelBackend']

# SERVER SETTINGS
SERVER_URL = parser.get('demotime', 'server_url')

SITE_ID = 1

# DemoTime Specific Settings
DT_PROD = parser.get('demotime', 'dt_prod')
DEFAULT_REMINDER_DAYS = int(parser.get('demotime', 'default_reminder_days'))

SENDFILE_BACKEND = 'sendfile.backends.nginx'
SENDFILE_ROOT = MEDIA_ROOT
SENDFILE_URL = '/protected'

# Celery Setup
BROKER_URL = 'amqp://demotime:demotime@rmq/demotime'
CELERY_RESULT_BACKEND = 'rpc://demotime:demotime@rmq'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ALWAYS_EAGER = not DT_PROD

if parser.has_section('email'):
    EMAIL_HOST = parser.get('email', 'email_host')
    EMAIL_HOST_USER = parser.get('email', 'email_host_user')
    EMAIL_HOST_PASSWORD = parser.get('email', 'email_host_password')
    EMAIL_PORT = parser.get('email', 'email_port')
    EMAIL_USE_TLS = parser.get('email', 'email_use_tls').lower() == 'true'
