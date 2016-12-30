from django.db.models.signals import post_save
from django.contrib.auth.models import User

# pylint: disable=import-error
from .settings import Setting
from .events import EventType, Event
from .attachments import Attachment, attachment_filename
from .messages import Message, MessageBundle
from .reminders import Reminder
from .followers import Follower
from .reviewers import Reviewer
from .groups import GroupType, Group, GroupMember
from .projects import Project, ProjectGroup, ProjectMember
from .webhooks import WebHook
from .users import UserProfile, UserReviewStatus, UserProxy
from .comments import Comment, CommentThread
from .creator import Creator
from .issues import Issue
from .reviews import Review, ReviewRevision


def create_profile(sender, instance, created, raw, **kwargs):
    if created and not raw:
        UserProfile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)
