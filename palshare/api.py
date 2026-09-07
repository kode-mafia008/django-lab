"""The JSON half of the app. The other half is `views.py`.

Both import `visible_posts` from `queries.py`, so the rule about who may see
what is written once and applied twice. That is the whole point of Part 4.
"""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Follow, Like, Post, Save
from .permissions import IsAuthorOrReadOnly
from .queries import people, visible_posts
from .serializers import PersonSerializer, PostSerializer


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

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """Idempotent on purpose: liking twice is a no-op, not a 400.

        Double taps happen on every slow connection there has ever been.
        """
        post = self.get_object()
        try:
            # The inner `atomic()` is not decoration. A constraint violation
            # marks the *whole* surrounding transaction as broken, so without a
            # savepoint to roll back to, catching IntegrityError buys nothing —
            # the next query in the request dies with TransactionManagementError.
            with transaction.atomic():
                Like.objects.create(user=request.user, post=post)
                Post.objects.filter(pk=post.pk).update(like_count=post.like_count + 1)
        except IntegrityError:
            pass  # the unique constraint did its job
        return Response({"liked": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        post = self.get_object()
        deleted, _ = Like.objects.filter(user=request.user, post=post).delete()
        if deleted:
            Post.objects.filter(pk=post.pk).update(like_count=max(post.like_count - 1, 0))
        return Response({"liked": False}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        """Save and unsave are like and unlike with a different table.

        Named `save` on the viewset and nothing else — `Model.save` is a
        different method on a different object, and this is a route.
        """
        post = self.get_object()
        try:
            with transaction.atomic():  # see `like` for why the savepoint matters
                Save.objects.create(user=request.user, post=post)
        except IntegrityError:
            pass
        return Response({"saved": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unsave(self, request, pk=None):
        post = self.get_object()
        Save.objects.filter(user=request.user, post=post).delete()
        return Response({"saved": False}, status=status.HTTP_200_OK)


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
        target = self.get_object()
        if target == request.user:
            # The CheckConstraint would also stop this, with a 500. A 400 with
            # a sentence is the version a person can act on.
            return Response({"detail": "You cannot follow yourself."},
                            status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.get_or_create(follower=request.user, following=target)
        return Response({"following": True})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, username=None):
        Follow.objects.filter(follower=request.user, following=self.get_object()).delete()
        return Response({"following": False})
