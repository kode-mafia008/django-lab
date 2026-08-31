from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    
    class Meta:
        db_table = 'authors'
        ordering = ["name"]
    
    def __str__(self):
        return self.name
       
