from django import template

from demotime import models

register = template.Library()


@register.simple_tag
def reviewer_status(review, user):
    if isinstance(review, models.ReviewRevision):
        review = review.review
    try:
        status = models.Reviewer.objects.get(
            review=review,
            reviewer=user
        ).get_status_display()
    except models.Reviewer.DoesNotExist:
        status = ''

    return status


@register.simple_tag
def setting_value(project, setting_key):
    return models.Setting.objects.get_value(project, setting_key)
