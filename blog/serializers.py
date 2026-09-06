from rest_framework import serializers

from .models import Author


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name cannot be blank.")
        return name

    def validate_bio(self, value):
        if value:
            bio = value.strip()
            if not bio:
                raise serializers.ValidationError("Bio cannot be just empty spaces.")
            return bio
        return value