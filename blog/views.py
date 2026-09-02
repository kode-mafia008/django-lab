from django.shortcuts import render, get_object_or_404
from .models import Author

from rest_framework import viewsets
from .serializers import AuthorSerializer

from rest_framework.permissions import IsAuthenticatedOrReadOnly

from drf_spectacular.utils import extend_schema

def authors(request):
    authors = Author.objects.all()

    return render(request, "blog/author_list.html", {
        "authors": authors
    })


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)

    return render(request, "blog/author_detail.html", {
        "author": author
    })


@extend_schema(
    tags=["Authors"],
)
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]