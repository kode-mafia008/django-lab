



from . serializers import(
    UserSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView

class RegisterView(generics.CreateAPIView):
    queryset =User.objects.none()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_validd(raise_exception=true)
        user = serializer.save()
        return Response(UserSerializer(user).data,status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    serializer_class =  LoginSerializer
    permission_classes = [AllowAny]

class UserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, requested):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"error": "Refresh Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"error": "Token is invalid or expired"}, status = status.HTTP_400_BAD_REQUEST)
        return Response(status = status.HTTP_205_RESET_CONTENT)    