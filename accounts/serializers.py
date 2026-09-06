from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [ "id","username","email" ]


class RegisterSerializer(serializers.ModelSerializer):
    """Registration is the one endpoint an anonymous stranger may write to.

    Everything about it is therefore an allowlist:

    * `fields` names four columns. `User` has fifteen, and two of them are
      `is_staff` and `is_superuser`. A field that is not listed cannot be set,
      no matter what the JSON body contains — which is the whole defence
      against privilege escalation by extra key.
    * `password` is `write_only`, so it can go in and never comes back out.
    * `validate_password` runs Django's AUTH_PASSWORD_VALIDATORS, so "123456"
      is rejected here rather than becoming somebody's real password.
    """

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ["id","username","email","password"]

    def create(self, validated_data):
        # `create_user` hashes the password. Plain `User.objects.create`,
        # which ModelSerializer would call, stores it verbatim.
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # A JWT payload is signed, not encrypted: anyone holding the token can
        # base64-decode this and read it. Claims are for identification, never
        # for secrets — no email, no role you would not print on a badge.
        token['username'] = user.username
        return token


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        write_only=True,
        help_text="The refresh token to blacklist.",
    )
