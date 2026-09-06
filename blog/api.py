"""JSON API views for the blog app.

Kept apart from `blog/views.py`, which renders HTML. The two answer different
clients with different rules, and the only thing they share is the models —
so they share `models.py` and nothing else. Serializers live in
`serializers.py`; the HTML side's forms live in `forms.py`.

Three security decisions live in this file, and each one is a different layer:

1. `permission_classes` — who may call the endpoint, and who may change a row.
2. `get_queryset()`    — which rows exist at all, as far as this caller knows.
3. `perform_create()`  — which facts the server records rather than accepts.

Layer 2 is the one people skip. A permission class that returns 403 still
confirms the row exists; a queryset that excludes it returns 404 and confirms
nothing.
"""

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Author, Blog
from .permissions import IsOwnerOrReadOnly
from .serializers import AuthorSerializer, BlogSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Author`, backed by the `authors` table."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]


class BlogViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Blog`, backed by the `blogs` table."""

    serializer_class = BlogSerializer
    # Documentation, not a filter. drf-spectacular reads this attribute to work
    # out that `{id}` is an integer, and DRF ignores it entirely once
    # `get_queryset()` exists. Do not mistake it for the security boundary —
    # the method below is the security boundary.
    queryset = Blog.objects.all()
    # Both are checked. `IsAuthenticated` answers "may you be here"; the second
    # answers "may you touch this row". DRF ANDs the list together, and it runs
    # the object-level half only for views that call `get_object()`.
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """The rows this caller is allowed to know about.

        Everything reachable by pk is reachable through this queryset, so
        filtering here covers `retrieve`, `update` and `destroy` too — not just
        the list. A draft belonging to somebody else is a 404, not a 403.
        """
        # `select_related` collapses the per-row author lookup that serialising
        # the foreign key would otherwise trigger.
        visible = Blog.objects.select_related("author", "owner")
        return visible.filter(Q(published=True) | Q(owner=self.request.user))

    def perform_create(self, serializer):
        """Stamp the owner from the credential, never from the request body.

        `serializer.save(owner=...)` lands in `validated_data`, so it wins over
        anything the client sent — and `owner` is read-only in the serializer,
        so the client could not have sent it anyway. Two locks, one door.
        """
        serializer.save(owner=self.request.user)
