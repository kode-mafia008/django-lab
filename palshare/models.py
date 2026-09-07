from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Everything about a user that `auth.User` does not already hold.

    A OneToOne rather than a custom user model: swapping `AUTH_USER_MODEL`
    after the first migration is a rewrite, and this project is twelve hours
    old. `related_name="profile"` makes it `request.user.profile`.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="profile")
    bio = models.TextField(blank=True)
    # FileField, not ImageField: ImageField needs Pillow, and this project has
    # gone ten days without adding a dependency. The extension allowlist in
    # `validate_upload` is the validation ImageField would have given us, and
    # it is validation the person who wrote it understands.
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="posts")
    text = models.TextField()
    followers_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Counter caches. A feed of 20 posts that counts likes per row is 21
    # queries; this is one. Kept honest by updating them in the like/save
    # endpoints, never by hand.
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"


class Media(models.Model):
    KIND = [("image", "Image"), ("video", "Video")]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="posts/%Y/%m/")
    kind = models.CharField(max_length=5, choices=KIND, default="image")
    alt = models.CharField(max_length=200, blank=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="comments")
    # One level of replies, and the model says so: a reply cannot have replies
    # because nothing enforces it here except the serializer refusing.
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                               related_name="replies")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # The database enforces "one like per person per post". Checking in
        # Python instead loses the race between two taps on a slow connection.
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_like_per_user")]


class Save(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="saves")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_save_per_user")]


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="one_follow_per_pair"),
            # Nobody follows themselves. Cheaper here than in every view that
            # creates a Follow.
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")),
                                   name="no_self_follow"),
        ]


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="sent_messages")
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at"]
