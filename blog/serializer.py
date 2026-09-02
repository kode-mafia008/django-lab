from rest_framework import serializers
from .models import Author


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ["id", "name", "bio"]

    def validate_name(self, value):
        name = value.strip()

        if not name:
            raise serializers.ValidationError("Name cannot be empty.")

        return name