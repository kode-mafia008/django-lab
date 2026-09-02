from rest_framework import serializers
from .models import Author, Blog


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'bio'
        ]
        read_only_fields = ['id']
        
        
class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'content',
            'author',
            'published',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
        
