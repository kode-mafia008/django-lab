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
    
    class Meta:
        model = User
        fields = ["id","username","email","password"]
    
class LoginSerializer(TokenObtainPairSerializer):

    def _init_(self, *args, **kwarges):
        super()._init_(*args, **kwarges)
        self.fields[self.username_field].required = False
        self.fields[self.username_field].help_text="Username or email address"
        self.fields["email"] = serializers. Emailfield(
            required=False,
                    write_only=True,
                    help_text=''' Email address, as an alternative to 'username' .''' )
            
    def validate(self, attrs):
    identifier =attrs .pop("email",None)
        
        @staticmethod
        def _resolve_username(identifier):
        if 
        

    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()