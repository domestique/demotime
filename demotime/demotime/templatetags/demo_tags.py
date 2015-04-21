from django import template

from demotime import models

register = template.Library()


@register.simple_tag
def review_status(review, request):
    if isinstance(review, models.ReviewRevision):
        review = review.review

    return models.Reviewer.objects.get(
        review=review,
        reviewer=request.user
    ).get_status_display()
