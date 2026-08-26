from django.db import models


class Author(models.Model):
    name = models.CharField(max_length = 118)
    bio  = models.TextField(blank = True)
    
    class Meta: 
        db_table = 'authors'
        