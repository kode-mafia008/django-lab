"""The JSON half of the app. The other half is `views.py`.

Both import `visible_posts` from `queries.py`, so the rule about who may see
what is written once and applied twice. That is the whole point of Part 4.
"""

from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Post
from .permissions import IsAuthorOrReadOnly
from .queries import people, visible_posts
from .serializers import PersonSerializer, PostSerializer
from .services import set_follow, set_like, set_save, set_share


class PostViewSet(viewsets.ModelViewSet):
    # Never used to serve a request — `get_queryset` overrides it. It is here so
    # drf-spectacular can find the model at schema-generation time, when there
    # is no `request.user` to filter by.
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        return visible_posts(self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # Every one of these is two lines because the rule lives in `services.py`,
    # which the HTML views call too. Idempotent on purpose: liking twice is a
    # no-op, not a 400, because double taps happen on every slow connection
    # there has ever been.

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        set_like(request.user, self.get_object(), True)
        return Response({"liked": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        set_like(request.user, self.get_object(), False)
        return Response({"liked": False}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        """Named `save` on the viewset and nothing else — `Model.save` is a
        different method on a different object, and this is a route."""
        set_save(request.user, self.get_object(), True)
        return Response({"saved": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unsave(self, request, pk=None):
        set_save(request.user, self.get_object(), False)
        return Response({"saved": False}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        set_share(request.user, self.get_object(), True)
        return Response({"shared": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unshare(self, request, pk=None):
        set_share(request.user, self.get_object(), False)
        return Response({"shared": False}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.none()  # see PostViewSet
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]
    # A profile URL says `/u/kaushal/`, not `/u/7/`.
    lookup_field = "username"

    def get_queryset(self):
        return people(self.request.user, User.objects.select_related("profile"))

    @action(detail=True, methods=["post"])
    def follow(self, request, username=None):
        try:
            set_follow(request.user, self.get_object(), True)
        except ValueError as error:
            # The CheckConstraint would also stop this, with a 500. A 400 with
            # a sentence is the version a person can act on.
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"following": True})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, username=None):
        set_follow(request.user, self.get_object(), False)
        return Response({"following": False})
