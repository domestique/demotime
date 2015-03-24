from django.conf.urls import patterns, url


urlpatterns = patterns('demotime.views',
    url('^$', 'index', name='index'),
    url('^create/$', 'review_form_view', name='create-review'),
    url('^review/(?P<pk>[\d]+)/$', 'review_detail', name='review-detail'),
)
