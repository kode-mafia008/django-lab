from django.conf import settings
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class Blog(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="blogs")

    # `author` is attribution: whose byline goes on the post. The client picks it.
    # `owner` is the security fact: which account is allowed to change this row.
    # The client never picks that — the server records it from the credential.
    #
    # Nullable because rows written before today have no owner. That is on
    # purpose: an unowned row matches nobody, so every ownership check fails
    # closed rather than open.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blogs",
        null=True,
        blank=True,
        editable=False,
    )
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blogs"
        ordering = ["-created_at"]
