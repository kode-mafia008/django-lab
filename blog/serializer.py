from rest_framework import serializers
from .models import Author

class AutherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'bio']
        read_only_fields = ['if']

class LoginResponseserializer(serializers.Serializer):
    access = serializers.CharField()
    Refresh = serializers.CharField()
    user = serializers.CharField()