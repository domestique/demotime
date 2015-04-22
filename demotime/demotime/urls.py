from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy


# General
urlpatterns = patterns('demotime.views',
    url('^$', 'index_view', name='index'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^addons/$', TemplateView.as_view(template_name='addons.html'), name='addons'),
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
    url(r'review/list/$', 'review_list_view', name='review-list'),
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
    url(
        r'^accounts/password/reset/$',
        'django.contrib.auth.views.password_reset',
        {
            'template_name': 'registration/password_reset_request.html',
            'post_reset_redirect': reverse_lazy('password_reset_done'),
        },
        name='password-reset'
    ),
    url(
        r'^accounts/password/reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_reset_submitted.html'},
        name='password_reset_done'
    ),
    url(
        r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'registration/password_reset_confirmation.html'},
        name='password_reset_confirm'
    ),
    url(
        r'^accounts/password/reset/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'registration/password_reset_completed.html'},
        name='password_reset_complete'
    ),
)
