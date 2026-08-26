from django.db import models

class Author(models.Model):
    Name = models.CharField(max_length=175)
    Title = models.TextField(blank=True)

    class Meta:
        db_table = 'authors'

# Create your models here.
