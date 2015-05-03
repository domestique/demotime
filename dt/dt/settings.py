"""
Django settings for dt project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'zf3o4tx%22pzoauflj+z2=$l2@g&$656!7d5ir)hdj4g!mv8$%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

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
    # Third Party Libs
    'macros',
    'registration',
    'django_markdown',
    # Our libs
    'demotime',
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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# CUSTOM DJANGO SETTINGS
TEMPLATE_CONTEXT_PROCESSORS = (
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
)


# MEDIA SETTINGS
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# TEST SETTINGS
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=demotime',
    '--logging-filter=-django.db.backends.schema',
]

# MAIL_SETTINGS
DEFAULT_FROM_EMAIL = 'system@demotyme.com'

# ACCOUNT SETTINGS
LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7

# SERVER SETTINGS
SERVER_URL = os.environ.get('DT_URL', 'localhost:8000')

# MARKDOWN SETTINGS
MARKDOWN_EDITOR_SKIN = 'simple'
MARKDOWN_EXTENSIONS = 'extra', 'codehilite'
MARKDOWN_EXTENSION_CONFIGS = {
    'codehilite': {
        'linenums': False,
    }
}

DT_PROD = os.environ.get('DT_PROD', '').lower() == 'true'

if DT_PROD:
    try:
        from prod_settings import *
    except ImportError:
        pass
