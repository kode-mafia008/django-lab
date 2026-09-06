from django.conf import settings
from django.db import models

# Create your models here.

class Post(models.Model):
    """
    A social-media post created by a user.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    
    content = models.TextField(blank=True)
    
    is_archived = models.BooleanField(default=False)
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]
        
    def __str__(self):
        return f"Post #{self.pk} by {self.author}"
    


class PostMedia(models.Model):
    """
    Images/videos attached to a post.

    A single post can have multiple media files.
    """
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="media",
    )
    
    file = models.FileField(
        upload_to="posts/%Y/%m/%d/"
    )
    
    
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["created_at"]
        
    
    def __str__(self):
        return f"{self.media_type} - Post #{self.post_id}"
    

class Comment(models.Model):
    """
    A comment on a post.

    parent=None     -> normal comment
    parent=<comment> -> reply to another comment
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["parent", "created_at"]),
        ]
        
    def __str__(self):
        return f"Comment #{self.pk} by {self.author}"
    
    
class Like(models.Model):
    """
    Records a user's like on a post.

    A user can like a particular post only once.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_post_like",
            )
        ]
    
    def __str__(self):
        return f"{self.user} liked Post #{self.post_id}"
    
    
class SavedPost(models.Model):
    """
    Records posts saved by users.

    A user can save a particular post only once.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_posts",
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="saved_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_saved_post",
            )
        ]

    def __str__(self):
        return f"{self.user} saved Post #{self.post_id}"


class Share(models.Model):
    """
    Records a post share.

    Multiple users can share the same post.
    The same user can technically share a post more than once.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shares",
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="shares",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} shared Post #{self.post_id}"