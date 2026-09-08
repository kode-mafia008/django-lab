"""The JSON half of the app. The other half is `views.py`.

Both import `visible_posts` from `queries.py`, so the rule about who may see
what is written once and applied twice. That is the whole point of Part 4.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Post
from .permissions import IsAuthorOrReadOnly
from .queries import people, visible_posts
from .serializers import PersonSerializer, PostSerializer
from .services import (reaction_summary, set_follow, set_like, set_reaction,
                       set_save, set_share)


class PostViewSet(viewsets.ModelViewSet):
    # Never used to serve a request — `get_queryset` overrides it. It is here so
    # drf-spectacular can find the model at schema-generation time, when there
    # is no `request.user` to filter by.
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    # Liking someone else's post is the entire point of liking. Applying
    # `IsAuthorOrReadOnly` to the whole viewset made every interaction below a
    # 403 unless you were reacting to yourself — the HTML pages had no such
    # rule, so the page and the API disagreed about a write, which is the one
    # thing `services.py` exists to prevent.
    #
    # `IsAuthorOrReadOnly` is about *editing a row*, so it applies to the three
    # actions that edit a row and to nothing else.
    INTERACTIONS = {"like", "unlike", "save", "unsave", "share", "unshare", "react"}

    def get_permissions(self):
        if self.action in self.INTERACTIONS:
            return [IsAuthenticated()]
        return super().get_permissions()

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

    @action(detail=True, methods=["post"])
    def react(self, request, pk=None):
        """`{"emoji": "\U0001f44d"}` sets it, the same emoji again clears it,
        and `{"emoji": null}` clears it outright — the page's three behaviours,
        because both call the same `set_reaction`.
        """
        post = self.get_object()
        try:
            emoji = set_reaction(request.user, post, request.data.get("emoji") or None)
        except DjangoValidationError as exc:
            # Django's ValidationError is not DRF's, and uncaught it is a 500
            # where a 400 belongs.
            raise serializers.ValidationError({"emoji": exc.messages})
        # Refetched, because `reaction_summary` reads the prefetch and the row
        # it is counting was just written.
        post = self.get_queryset().get(pk=post.pk)
        return Response({"emoji": emoji, "reactions": reaction_summary(post, request.user)},
                        status=status.HTTP_200_OK)


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
