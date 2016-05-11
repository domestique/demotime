from django.conf.urls import url
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.views import (
    login,
    logout_then_login,
    password_reset,
    password_reset_complete,
    password_reset_confirm,
    password_reset_done,
)

from demotime.views import (
    files,
    groups,
    index_view,
    messages,
    profile,
    projects,
    reviews,
    users,
)


# General
urlpatterns = [
    url('^$', index_view, name='index'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^help/$', TemplateView.as_view(template_name='demotime/help.html'), name='help')
]

# Groups
urlpatterns += [
    url(r'^groups/$', groups.group_list, name='group-list'),
    url(r'^groups/create/$', groups.manage_group, name='group-manage'),
    url(r'^groups/edit/(?P<group_slug>[\w-]+)/$', groups.manage_group, name='group-manage'),
]

# Reviews
urlpatterns += [
    # Review Creation
    url(r'^(?P<proj_slug>[\w-]+)/create/$', reviews.review_form_view, name='create-review'),
    # DT-1234 redirect view
    url(r'^(?i)DT-(?P<pk>[\d]+)/$', reviews.dt_redirect_view, name='dt-redirect'),
    # Review Detail Page
    url(
        r'^(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/$',
        reviews.review_detail,
        name='review-detail'
    ),
    # Review Revision Detail Page
    url(
        r'^(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/rev/(?P<rev_num>[\d]+)/$',
        reviews.review_detail,
        name='review-rev-detail'
    ),
    # Review Edit Page
    url(r'^(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/edit/$', reviews.review_form_view, name='edit-review'),
    # Reviewer Approval/Rejection
    url(
        r'^(?P<proj_slug>[\w-]+)/review/(?P<review_pk>[\d]+)/reviewer-status/(?P<reviewer_pk>[\d]+)/$',
        reviews.reviewer_status_view,
        name='update-reviewer-status',
    ),
    # Review State Update (open/closed)
    url(
        r'^(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/update-state/$',
        reviews.review_state_view,
        name='update-review-state'
    ),
    url(r'^review/list/$', reviews.review_list_view, name='review-list'),
    url(r'^review/search/$', reviews.review_json_view, name='reviews-json'),
    url(r'^(?P<proj_slug>[\w-]+)/review/search/$', reviews.review_json_view, name='reviews-json'),
]

# Comments
urlpatterns += [
    url(r'^comment/update/(?P<pk>[\d]+)/$', reviews.update_comment_view, name='update-comment'),
    url(
        r'^comment/(?P<comment_pk>[\d]+)/attachment/(?P<attachment_pk>[\d]+)/update/$',
        reviews.delete_comment_attachment_view,
        name='update-comment-attachment'
    ),
]

# Messages
urlpatterns += [
    url(r'^inbox/$', messages.inbox_view, name='inbox'),
    url(r'^message/(?P<pk>[\d]+)/$', messages.msg_detail_view, name='message-detail'),
    url(r'^messages/$', messages.messages_json_view, name='messages-json'),
    url(
        r'^messages/(?P<review_pk>[\d]+)/$',
        messages.messages_json_view,
        name='messages-json'
    ),
]

# Files
urlpatterns += [
    url(r'^file/(?P<file_path>.+)$', files.user_media_view, name='user-media'),
]

# Users
urlpatterns += [
    url(r'^accounts/login/$', login, name='login'),
    url(r'^accounts/logout/$', logout_then_login, name='logout'),
    url(r'^accounts/profile/(?P<pk>[\d]+)/$', profile.profile_view, name='profile'),
    url(r'^accounts/profile/(?P<pk>[\d]+)/edit/$', profile.edit_profile_view, name='edit-profile'),
    url(
        r'^accounts/password/reset/$',
        password_reset,
        {
            'template_name': 'registration/password_reset_request.html',
            'post_reset_redirect': reverse_lazy('password_reset_done'),
        },
        name='password-reset'
    ),
    url(
        r'^accounts/password/reset/done/$',
        password_reset_done,
        {'template_name': 'registration/password_reset_submitted.html'},
        name='password_reset_done'
    ),
    url(
        r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        password_reset_confirm,
        {'template_name': 'registration/password_reset_confirmation.html'},
        name='password_reset_confirm'
    ),
    url(
        r'^accounts/password/reset/complete/$',
        password_reset_complete,
        {'template_name': 'registration/password_reset_completed.html'},
        name='password_reset_complete'
    ),
    url(r'^users/$', users.user_api, name='user-api'),
]

# Projects
urlpatterns += [
    url(r'projects/$', projects.project_json, name='project-json'),
    url(r'(?P<proj_slug>[-\w]+)/admin/edit/$', projects.project_admin, name='project-admin'),
    url(r'(?P<proj_slug>[-\w]+)/admin/$', projects.project_detail, name='project-detail'),
    url(r'(?P<proj_slug>[-\w]+)/$', projects.project_dashboard, name='project-dashboard'),
]
