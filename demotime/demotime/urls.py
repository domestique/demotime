from django.conf.urls import patterns, url


urlpatterns = patterns('demotime.views',
    # General
    url('^$', 'index', name='index'),

    # Reviews
    url('^create/$', 'review_form_view', name='create-review'),
    url('^review/(?P<pk>[\d]+)/$', 'review_detail', name='review-detail'),
)

# Accounts
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout')
)
