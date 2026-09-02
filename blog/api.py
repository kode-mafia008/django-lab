"""JSON API views for the blog app.

Kept apart from `blog/views.py`, which renders HTML. The two answer different
clients with different rules, and the only thing they share is the models —
so they share `models.py` and nothing else. Serializers live in
`serializers.py`; the HTML side's forms live in `forms.py`.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Author, Blog
from .serializers import AuthorSerializer, BlogSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Author`, backed by the `authors` table."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]


class BlogViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Blog`, backed by the `blogs` table."""

    # `select_related` collapses the per-row author lookup that serialising
    # the foreign key would otherwise trigger.
    queryset = Blog.objects.select_related("author")
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated]
