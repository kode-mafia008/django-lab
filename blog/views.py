from django.shortcuts import get_object_or_404, render

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Author
from .serializers import AuthorSerializer


def author_list(request):
    authors = Author.objects.order_by("name")

    return render(
        request,
        "blog/author_list.html",
        {"authors": authors},
    )


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)

    return render(
        request,
        "blog/author_detail.html",
        {"author": author},
    )


class AuthorListView(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]