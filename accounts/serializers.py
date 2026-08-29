from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', )
        
class RegistrationSerializer(serializers.ModelSerializer):
    password=serializers.CharField(
        write_only=True,
        validators=[validate_password]
        )
    
    class Meta:
        model=User
        fields=["id","username","email","password"]
       
class LoginSerializer(TokenObtainPairSerializer):
    
    def get_token(cls, user):
        token=super().get_token(user)
        token["username"]=user.username
        return token
    
    def validate(self,attrs):
        data=super().validate(attrs)
        data["user"]=UserSerializer(self.user).data  
        return data
    
class logoutSerializer(serializers.Serializer):
    access=serializers.CharField()
    refresh=serializers.CharField()
    user=UserSerializer()          