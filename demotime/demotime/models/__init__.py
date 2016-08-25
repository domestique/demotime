from django.db.models.signals import post_save
from django.contrib.auth.models import User

from .attachments import Attachment, attachment_filename
from .comments import Comment, CommentThread
from .messages import Message, MessageBundle
from .reviews import Review, ReviewRevision
from .users import UserProfile, UserReviewStatus, UserProxy
from .reminders import Reminder
from .followers import Follower
from .reviewers import Reviewer
from .groups import GroupType, Group, GroupMember
from .projects import Project, ProjectGroup, ProjectMember
from .webhooks import WebHook
from .settings import Setting
from .events import EventType, Event


def create_profile(sender, instance, created, raw, **kwargs):
    if created and not raw:
        UserProfile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)
