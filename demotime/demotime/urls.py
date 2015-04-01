from django.conf.urls import patterns, url


urlpatterns = patterns('demotime.views',
    # General
    url('^$', 'index_view', name='index'),

    # Reviews
    url('^create/$', 'review_form_view', name='create-review'),
    url('^review/(?P<pk>[\d]+)/$', 'review_detail', name='review-detail'),
    url('^review/(?P<pk>[\d]+)/rev/(?P<rev_pk>[\d]+)/$$', 'review_detail', name='review-rev-detail'),
    url('^review/(?P<pk>[\d]+)/edit/$', 'review_form_view', name='edit-review'),
)

# Accounts
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout')
)
