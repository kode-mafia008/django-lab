from .serializers import (
    UserSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from drf_spectacular.utils import OpenApiResponse,extend_schema
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.none()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self,request,*args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data,status=status.HTTP_201_CREATED)

@extend_schema(
    summary="Log in and get a token obtain pair",
    description=(
        "Exchange credentials for an access token and refresh token"
    ),
    responses={200:LoginResponseSerializer}
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class UserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"error":"Refresh Token is required"},status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"error":"Token is invalid or expired"},status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)