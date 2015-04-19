import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url

admin.autodiscover()

urlpatterns = patterns('',
    # DT needs to be on top, otherwise django-reg tramples some urls
    url('', include('demotime.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url('^markdown/', include('django_markdown.urls')),
)

if not os.environ.get('DT_PROD'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
