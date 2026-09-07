"""Database entities for the PalShare UI.

Views must enforce access permissions and call full_clean() for model validation.
Counts and viewer-specific flags in demo.py are query/serializer projections.
The *_id annotations describe attributes Django creates for foreign keys;
they let Pylance recognize those attributes without changing database fields.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, Q


def validate_text(value):
    if not value.strip():
        raise ValidationError("Text cannot be empty or whitespace.")


class Profile(models.Model):
    user_id: int

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                primary_key=True, related_name="profile")
    name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.FileField(upload_to="palshare/avatars/", blank=True,
                              validators=[FileExtensionValidator(
                                  ["jpg", "jpeg", "png", "gif", "webp"])])
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name or self.user.get_username()


class Post(models.Model):
    author_id: int

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="palshare_posts")
    # The write service must require text or media after processing all uploads.
    text = models.TextField(blank=True)
    followers_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["created_at", "id"]),
            models.Index(fields=["author", "created_at", "id"]),
        ]

    def __str__(self):
        return f"{self.author}: {self.text[:50]}"


class Media(models.Model):
    post_id: int

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="palshare/posts/%Y/%m/")
    kind = models.CharField(max_length=5, choices=Kind.choices)
    alt = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["post", "position"], name="ps_media_position_unique"),
            models.CheckConstraint(condition=Q(position__gte=0, position__lte=3),
                                   name="ps_media_four_slots"),
            models.CheckConstraint(condition=Q(kind__in=["image", "video"]),
                                   name="ps_media_kind_valid"),
        ]


class Comment(models.Model):
    post_id: int
    author_id: int
    parent_id: int | None

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="palshare_comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                               related_name="replies")
    text = models.TextField(validators=[validate_text])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["post", "parent", "created_at", "id"])]
        constraints = [models.CheckConstraint(condition=~Q(parent=F("id")),
                                              name="ps_comment_not_own_parent")]

    def clean(self):
        super().clean()
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).values("post_id", "parent_id").first()
            if original and (original["post_id"] != self.post_id or
                             original["parent_id"] != self.parent_id):
                raise ValidationError("A comment cannot move to another post or parent.")
        if self.parent_id:
            parent = type(self).objects.filter(pk=self.parent_id).first()
            if parent and (parent.post_id != self.post_id or parent.parent_id is not None):
                raise ValidationError({"parent": "Replies must reference a top-level comment on the same post."})

    def __str__(self):
        return self.text[:50]


class PostInteraction(models.Model):
    user_id: int
    post_id: int

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="palshare_%(class)s_records")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="%(class)s_records")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(fields=["user", "post"],
                                                name="ps_%(class)s_user_post_unique")]


class Like(PostInteraction):
    pass


class Save(PostInteraction):
    class Meta(PostInteraction.Meta):
        abstract = False
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "created_at", "id"])]


class Share(PostInteraction):
    """One share per user and original post; no quote-post semantics."""


class CommentLike(models.Model):
    user_id: int
    comment_id: int

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="palshare_comment_likes")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "comment"],
                                                name="ps_comment_like_unique")]


class Follow(models.Model):
    follower_id: int
    following_id: int

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="palshare_following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="palshare_followers")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["follower", "status"]),
                   models.Index(fields=["following", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="ps_follow_pair_unique"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="ps_follow_not_self"),
            models.CheckConstraint(
                condition=(Q(status="pending", accepted_at__isnull=True) |
                           Q(status="accepted", accepted_at__isnull=False)),
                name="ps_follow_acceptance_valid"),
        ]


class Conversation(models.Model):
    """Direct chat. Supply the smaller user ID as participant_one."""

    participant_one_id: int
    participant_two_id: int

    participant_one = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        related_name="palshare_conversations_one")
    participant_two = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        related_name="palshare_conversations_two")
    created_at = models.DateTimeField(auto_now_add=True)
    # Sending a message must update this in the same transaction.
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["participant_one", "updated_at"]),
                   models.Index(fields=["participant_two", "updated_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(participant_one__lt=F("participant_two")),
                                   name="ps_conversation_ordered_pair"),
            models.UniqueConstraint(fields=["participant_one", "participant_two"],
                                    name="ps_conversation_pair_unique"),
        ]

    def clean(self):
        super().clean()
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).values(
                "participant_one_id", "participant_two_id").first()
            if original and (original["participant_one_id"] != self.participant_one_id or
                             original["participant_two_id"] != self.participant_two_id):
                raise ValidationError("Conversation participants cannot be changed.")


class Message(models.Model):
    conversation_id: int
    sender_id: int

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="palshare_sent_messages")
    text = models.TextField(validators=[validate_text])
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at", "id"]
        indexes = [models.Index(fields=["conversation", "sent_at", "id"]),
                   models.Index(fields=["conversation", "read_at", "sender"])]
        constraints = [models.CheckConstraint(
            condition=Q(read_at__isnull=True) | Q(read_at__gte=F("sent_at")),
            name="ps_message_read_after_sent")]

    def clean(self):
        super().clean()
        if self.pk:
            original = type(self).objects.filter(pk=self.pk).values("sender_id", "conversation_id").first()
            if original and (original["sender_id"] != self.sender_id or
                             original["conversation_id"] != self.conversation_id):
                raise ValidationError("Message sender and conversation cannot be changed.")
        if self.conversation_id and self.sender_id:
            conversation = Conversation.objects.filter(pk=self.conversation_id).first()
            if conversation and self.sender_id not in (
                    conversation.participant_one_id, conversation.participant_two_id):
                raise ValidationError({"sender": "Sender must belong to this conversation."})

    def __str__(self):
        return self.text[:50]


class AssistantThread(models.Model):
    user_id: int

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="palshare_assistant_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at", "id"])]


class AssistantTurn(models.Model):
    thread_id: int

    class Role(models.TextChoices):
        USER = "user", "You"
        ASSISTANT = "assistant", "Assistant"

    thread = models.ForeignKey(AssistantThread, on_delete=models.CASCADE, related_name="turns")
    position = models.PositiveIntegerField()
    role = models.CharField(max_length=9, choices=Role.choices)
    text = models.TextField(validators=[validate_text])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["thread", "position"], name="ps_assistant_turn_position"),
            models.CheckConstraint(condition=Q(role__in=["user", "assistant"]),
                                   name="ps_assistant_role_valid"),
        ]
