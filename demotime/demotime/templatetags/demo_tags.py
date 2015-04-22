from django import template

from demotime import models

register = template.Library()


@register.simple_tag
def reviewer_status(review, user):
    if isinstance(review, models.ReviewRevision):
        review = review.review

    return models.Reviewer.objects.get(
        review=review,
        reviewer=user
    ).get_status_display()
