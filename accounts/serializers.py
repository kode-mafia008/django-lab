from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User 
        fields = [ "id","username","email" ]
        
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )


    def create(self,validated_data):
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = ["id","username","email","password"]

class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        write_only=True,
        help_text="Refresh token to be blacklisted"
    )
    
        