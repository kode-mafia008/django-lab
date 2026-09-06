from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.none()
    serializer_class = RegisterSerializer
    # The one endpoint that has to be open. `AllowAny` here is a decision, not
    # an oversight — which is why it is written out rather than inherited.
    permission_classes = [AllowAny]
    # ...and an open endpoint that writes rows needs a rate limit. The "auth"
    # rate is set in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Log in and get a token obtain pair",
    description=("Exchange credentials for an access token and refresh token"),
    responses={200: LoginResponseSerializer},
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    # Without this, a password is a 30-millisecond guess that can be repeated
    # forever. With it, an attacker gets five tries a minute per IP.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class UserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # The object comes from the token, not a pk in the URL.
        return self.request.user


@extend_schema(
    summary="Log out",
    description="Blacklists the supplied refresh token so it can no longer be exchanged.",
    responses={205: OpenApiResponse(description="Refresh token blacklisted")},
)
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response(
                {"error": "Token is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)
