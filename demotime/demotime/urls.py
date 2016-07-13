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
    webhooks,
)


# General
urlpatterns = [
    url('^$', index_view, name='index'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^terms-of-use/$', TemplateView.as_view(template_name='terms_of_use.html'), name='terms-of-use'),
    url(r'^privacy-policy/$', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy-policy'),
    url(r'^help/$', TemplateView.as_view(template_name='demotime/help.html'), name='help')
]

# Admin urls
urlpatterns += [
    url(r'^admin/groups/$', groups.group_list, name='group-list'),
    url(r'^admin/groups/create/$', groups.manage_group, name='group-manage'),
    url(r'^admin/groups/edit/(?P<group_slug>[\w-]+)/admins$', groups.manage_group_admins, name='group-manage-admins'),
    url(r'^admin/groups/edit/(?P<group_slug>[\w-]+)/$', groups.manage_group, name='group-manage'),
    url(r'^admin/group-types/create/$', groups.manage_group_type, name='group-type-manage'),
    url(r'^admin/group-types/edit/(?P<slug>[\w-]+)/$', groups.manage_group_type, name='group-type-manage'),
    url(r'^admin/projects/create/$', projects.project_admin, name='project-create'),
]

# Reviews
urlpatterns += [
    # Review Creation
    url(r'^reviews/(?P<proj_slug>[\w-]+)/create/$', reviews.review_form_view, name='create-review'),
    # DT-1234 redirect view
    url(r'^(?i)DT-(?P<pk>[\d]+)/$', reviews.dt_redirect_view, name='dt-redirect'),
    # Review Json Endpoint
    url(
        r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/json/$',
        reviews.review_json_view,
        name='review-json'
    ),
    # Review Detail Page
    url(
        r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/$',
        reviews.review_detail,
        name='review-detail'
    ),
    # Review Revision Detail Page
    url(
        r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/rev/(?P<rev_num>[\d]+)/$',
        reviews.review_detail,
        name='review-rev-detail'
    ),
    # Review Edit Page
    url(r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/edit/$', reviews.review_form_view, name='edit-review'),
    # Reviewer Approval/Rejection
    url(
        r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<review_pk>[\d]+)/reviewer-status/(?P<reviewer_pk>[\d]+)/$',
        reviews.reviewer_status_view,
        name='update-reviewer-status',
    ),
    # Review State Update (open/closed)
    url(
        r'^reviews/(?P<proj_slug>[\w-]+)/review/(?P<pk>[\d]+)/update-state/$',
        reviews.review_state_view,
        name='update-review-state'
    ),
    url(r'^reviews/list/$', reviews.review_list_view, name='review-list'),
    url(r'^reviews/search/$', reviews.review_search_json_view, name='reviews-search-json'),
    url(r'^reviews/(?P<proj_slug>[\w-]+)/search/$', reviews.review_search_json_view, name='reviews-search-json'),
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
    url(r'^file/profile/(?P<file_path>.+)$', files.user_profile_media_view, name='user-profile-media'),
    url(r'^file/(?P<pk>[\d]+)$', files.user_media_view, name='user-media'),
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
    url(
        r'projects/(?P<proj_slug>[-\w]+)/admin/hooks/create/$',
        webhooks.manage_hooks,
        name='webhook-create'
    ),
    url(
        r'projects/(?P<proj_slug>[-\w]+)/admin/hooks/edit/(?P<hook_pk>[\d]+)/$',
        webhooks.manage_hooks,
        name='webhook-edit'
    ),
    url(r'projects/(?P<proj_slug>[-\w]+)/admin/edit/$', projects.project_admin, name='project-admin'),
    url(r'projects/(?P<proj_slug>[-\w]+)/admin/$', projects.project_detail, name='project-detail'),
    url(r'projects/(?P<proj_slug>[-\w]+)/$', projects.project_dashboard, name='project-dashboard'),

]
