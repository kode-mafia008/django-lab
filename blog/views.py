from django.shortcuts import get_object_or_404, render

from rest_framework import viewsets

from .serializers import AuthorSerializer, BlogSerializer
from .models import Author, blog

from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_spectacular.utils import extend_schema


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})


@extend_schema(tags=["Authors"])
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=["Blogs"])
class BlogViewSet(viewsets.ModelViewSet):
    queryset = blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated]