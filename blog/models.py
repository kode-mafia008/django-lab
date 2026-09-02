from django.db import models

class Blog(models.Model):
    # Primary Key (auto-increment)
    id = models.AutoField(primary_key=True)

    # Blog fields
    title = models.CharField(max_length=200)          # Blog title
    content = models.TextField()                      # Blog content
    author = models.CharField(max_length=100)         # Author name
    published = models.BooleanField(default=False)    # Publish status

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)      # Update on save

    def __str__(self):
        return self.title
