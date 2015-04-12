from django.conf.urls import patterns, url


# General
urlpatterns = patterns('demotime.views',
    url('^$', 'index_view', name='index'),
)

# Reviews
urlpatterns += patterns('demotime.views.reviews',
    url(r'^create/$', 'review_form_view', name='create-review'),
    url(r'^review/(?P<pk>[\d]+)/$', 'review_detail', name='review-detail'),
    url(r'^review/(?P<pk>[\d]+)/rev/(?P<rev_pk>[\d]+)/$', 'review_detail', name='review-rev-detail'),
    url(r'^review/(?P<pk>[\d]+)/edit/$', 'review_form_view', name='edit-review'),
    url(
        r'^review/(?P<review_pk>[\d]+)/reviewer-status/(?P<reviewer_pk>[\d]+)/$',
        'reviewer_status_view',
        name='update-reviewer-status',
    ),
    url(r'review/(?P<pk>[\d]+)/update-state/$', 'review_state_view', name='update-review-state'),
)

# Messages
urlpatterns += patterns('demotime.views.messages',
    url(r'^inbox/$', 'inbox_view', name='inbox'),
    url(r'^message/(?P<pk>[\d]+)/$', 'msg_detail_view', name='message-detail'),
)

# Accounts
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^accounts/profile/(?P<pk>[\d]+)/$', 'demotime.views.users.profile_view', name='profile'),
    url(r'^accounts/profile/(?P<pk>[\d]+)/edit/$', 'demotime.views.users.edit_profile_view', name='edit-profile'),
)
