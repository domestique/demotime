from django.db.models.signals import post_save
from django.contrib.auth.models import User

from .attachments import Attachment, attachment_filename
from .comments import Comment, CommentThread
from .messages import Message
from .reviews import Review, ReviewRevision, Reviewer
from .users import UserProfile, UserReviewStatus


def create_profile(sender, instance, created, raw, **kwargs):
    if created and not raw:
        UserProfile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)
