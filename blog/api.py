from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Author
from .serializers import AuthorSerializer


@extend_schema_view(
    list=extend_schema(summary="List authors", description="Public. Supports ?search= on name and bio."),
    retrieve=extend_schema(summary="Retrieve one author"),
    create=extend_schema(summary="Create an author", description="Requires a Bearer access token."),
    update=extend_schema(summary="Replace an author"),
    partial_update=extend_schema(summary="Update some fields of an author"),
    destroy=extend_schema(summary="Delete an author"),
)
class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Author`, backed by the `authors` table."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "bio"]
    ordering_fields = ["id", "name"]