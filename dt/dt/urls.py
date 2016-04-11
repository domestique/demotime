from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url

from demotime import urls as demotime_urls
from registration.backends.default import urls as registration_urls

admin.autodiscover()

urlpatterns = [
    # DT needs to be on top, otherwise django-reg tramples some urls
    url('', include(demotime_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(registration_urls))
]

if not settings.DT_PROD:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
