from django.db import models

class blog(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blogs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]

    def __str__(self):
        return self.name
