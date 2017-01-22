from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.views.defaults import page_not_found, server_error

from demotime import urls as demotime_urls
from registration.backends.default import urls as registration_urls

admin.autodiscover()

urlpatterns = [
    # DT needs to be on top, otherwise django-reg tramples some urls
    url('', include(demotime_urls)),
    url(r'^djadmin/', include(admin.site.urls)),
    url(r'^accounts/', include(registration_urls))
]

if not settings.DT_PROD:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        url(r'^400/$', TemplateView.as_view(template_name='400.html')),
        url(r'^403/$', TemplateView.as_view(template_name='403.html')),
        url(r'^404/$', page_not_found, {'exception': 'Http404'}),
        url(r'^500/$', server_error),
    ]
    if not settings.TEST_RUN:
        from silk import urls as silk_urls
        urlpatterns += [
            url(r'^silk/', include(silk_urls, namespace='silk')),
        ]
