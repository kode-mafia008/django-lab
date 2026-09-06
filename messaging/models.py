from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    Represents a DM conversation.

    A conversation can contain two users for the MVP,
    and the structure also allows group conversations later.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation #{self.pk}"


class ConversationMember(models.Model):
    """
    Connects users to conversations.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_member",
            )
        ]

        indexes = [
            models.Index(fields=["conversation", "user"]),
            models.Index(fields=["user", "conversation"]),
        ]

    def __str__(self):
        return (
            f"{self.user} in "
            f"Conversation #{self.conversation_id}"
        )


class Message(models.Model):
    """
    A message sent inside a conversation.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )

    content = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"]
            ),
            models.Index(
                fields=["sender", "created_at"]
            ),
        ]

    def __str__(self):
        return f"Message #{self.pk}"