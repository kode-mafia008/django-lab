from django.db import models
from django.conf import settings
# Create your models here.

class Profile(models.Model):
    """
    Additional profile information for a PalShare user.

    Authentication fields such as username, email and password
    remain in Django's built-in User model.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        
    )
    
    bio = models.TextField(
        blank=True,
        max_length=500,
    )
    
    avatar = models.ImageField(
        upload_to="profiles/avatars",
        blank=True,
        null=True,
    )
    
    cover_image = models.ImageField(
        upload_to="profiles/covers",
        blank=True,
        null=True,
    )
    
    location = models.CharField(
        max_length=150,
        blank=True
    )
    
    website = models.URLField(
        blank=True
    )
    
    is_private = models.BooleanField(
        default=False
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"