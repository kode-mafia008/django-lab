from django.contrib.auth.models import User

from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer, UserSerializer


@extend_schema(tags=["Authentication"])
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
    tags=["Authentication"],
    request=RegisterSerializer,
    responses={201: dict, 400: dict},
)
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully",
                    "username": user.username,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(TokenObtainPairView):

    @extend_schema(
        tags=["Authentication"],
        request=TokenObtainPairView.serializer_class,
        responses=TokenObtainPairView.serializer_class,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Authentication"])
class RefreshView(TokenRefreshView):
    pass


@extend_schema(tags=["Authentication"])
class VerifyView(TokenVerifyView):
    pass


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    tags=["Authentication"],
    request=RefreshTokenSerializer,
    responses={205: dict, 400: dict},
)
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        responses=UserSerializer,
    )
    def get(self, request):
        return Response(
            UserSerializer(request.user).data
        )