from django.urls import path
<<<<<<< HEAD
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserView,

)
from rest_framework_simplejwt.views import   (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/info/', UserView.as_view(), name='user-info'),
    path('refresh', TokenRefreshView.as_view(), name='refresh'),
    path('verify', TokenVerifyView.as_view(), name='verify'),
=======
from rest_framework_simplejwt.views import TokenRefreshView,TokenVerifyView
from .views import (
    LoginView,
    LogoutView,
    UserView,
    RegisterView,
)


urlpatterns = [
  path('register/',RegisterView.as_view(),name='register'),
  path('login/',LoginView.as_view(),name='login'),
  path('logout/',LogoutView.as_view(),name='logout'),
  path('user/info',UserView.as_view(),name='user-info'),
  path('refresh',TokenRefreshView.as_view(),name='refresh'),
  path('verify',TokenVerifyView.as_view(),name='verify'),
>>>>>>> d658b56fc2e2a24b5209bd35d33413a1bf3b4941
]