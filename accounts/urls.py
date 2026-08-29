from django.urls import path

from . import views

app_name = "accounts"
url_patterns = [
    path('', views.register, name='register')
]