"""One shape per thing, defined once and consumed twice.

The templates read `post.author.name`, `post.likes`, `post.liked`, `post.age`.
The models have `author.first_name`, `like_count`, no `liked` at all, and a
`created_at` that is a timestamp rather than a phrase. The serializers close
that gap — and because `views.py` renders through them too, the page and the
API cannot drift apart.

`demo.py` is the contract these match. Read the two side by side.
"""

from django.contrib.auth.models import User
from django.template.defaultfilters import date as date_filter
from django.utils.timesince import timesince
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from .models import Comment, Media, Message, Post


def initial(user):
    """The one-letter avatar every card and row renders.

    A letter, not an <img>: uploads are Part 6, and a layout that only looks
    right once media exists is a layout nobody can review in hour one.
    """
    return (user.get_full_name() or user.username or "?")[:1].upper()


def display_name(user):
    """`get_full_name()` alone renders an empty byline for anyone who signed up
    without a first name — which is everybody, at a workshop."""
    return user.get_full_name() or user.username


# `blog` already registers a component called "Author". Two different shapes
# under one name is a schema that lies about one of them.
@extend_schema_serializer(component_name="PalShareAuthor")
class AuthorSerializer(serializers.ModelSerializer):
    """A user as a byline: the fields a post card actually shows.

    Deliberately smaller than PersonSerializer. Nesting the big one inside a
    post costs two extra queries per row for follower counts nobody is looking
    at — twenty of them on a ten-post page.
    """

    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "name", "avatar"]

    def get_name(self, user) -> str:
        return display_name(user)

    def get_avatar(self, user) -> str:
        return initial(user)


# The component name is inherited along with everything else, so each subclass
# has to claim its own or they all register as "PalShareAuthor".
@extend_schema_serializer(component_name="PalSharePersonRow")
class PersonRowSerializer(AuthorSerializer):
    """One person in a list: search results, followers, following, suggestions.

    `is_following` is read off the annotation `queries.people()` adds, not
    computed here — a `SerializerMethodField` that queries is one query per
    row, and these are all rows.
    """

    bio = serializers.CharField(source="profile.bio", read_only=True, default="")
    is_following = serializers.BooleanField(read_only=True, default=False)

    class Meta(AuthorSerializer.Meta):
        fields = AuthorSerializer.Meta.fields + ["bio", "is_following"]


@extend_schema_serializer(component_name="PalSharePerson")
class PersonSerializer(PersonRowSerializer):
    """The profile header, where the follower counts are actually on screen.

    Two `.count()` calls per person — which is why this one stays on the
    profile page and `PersonRowSerializer` is what lists use.
    """

    followers = serializers.IntegerField(source="followers.count", read_only=True)
    following = serializers.IntegerField(source="following.count", read_only=True)
    post_count = serializers.IntegerField(source="posts.count", read_only=True)
    is_private = serializers.BooleanField(source="profile.is_private", read_only=True,
                                          default=False)
    is_me = serializers.SerializerMethodField()
    joined = serializers.SerializerMethodField()

    class Meta(PersonRowSerializer.Meta):
        fields = PersonRowSerializer.Meta.fields + [
            "followers", "following", "post_count", "is_private", "is_me", "joined",
        ]

    def get_is_me(self, user) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.pk == user.pk)

    def get_joined(self, user) -> str:
        return date_filter(user.date_joined, "F Y")


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "kind", "alt", "file"]


class PostSerializer(serializers.ModelSerializer):
    """Matches `post` in demo.py — the contract the templates already read."""

    author = AuthorSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    likes = serializers.IntegerField(source="like_count", read_only=True)
    comments = serializers.IntegerField(source="comment_count", read_only=True)
    # Read straight off the annotations `visible_posts()` adds. A
    # SerializerMethodField that queries is a query per row, and a feed is
    # nothing but rows.
    liked = serializers.BooleanField(read_only=True, default=False)
    saved = serializers.BooleanField(read_only=True, default=False)
    # Sharing is in `demo.py` and on the card, and is not a feature yet. Zero
    # is the honest answer; a field that quietly disappears is not.
    shares = serializers.IntegerField(read_only=True, default=0)
    # `created_at` is a timestamp for machines; `age` is a string for people.
    # One name for both is how a UI ends up printing an ISO 8601 string at a
    # human.
    age = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author", "text", "media", "followers_only",
                  "likes", "comments", "shares", "liked", "saved",
                  "age", "created_at", "updated_at"]
        # Everything the server owns. `author` is not in this list because it
        # is not in `fields` as a writable field at all — it is nested and
        # read-only, and the view sets it from the credential.
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_age(self, post) -> str:
        return f"{timesince(post.created_at)} ago"


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    # Comment likes are on the card and not in the schema. Same call as
    # `shares`: render the zero, do not pretend the field is not read.
    likes = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Comment
        fields = ["id", "author", "text", "age", "likes", "parent", "replies"]
        read_only_fields = ["id"]

    def get_age(self, comment) -> str:
        return f"{timesince(comment.created_at)} ago"

    def get_replies(self, comment) -> list:
        # One level, and no deeper: `_comment.html` renders replies inline and
        # does not recurse, so neither does this.
        if comment.parent_id is not None:
            return []
        return CommentSerializer(comment.replies.all(), many=True,
                                 context=self.context).data

    def validate_parent(self, parent):
        """Replies go one level deep. The model allows more; we do not."""
        if parent and parent.parent_id is not None:
            raise serializers.ValidationError("Reply to the comment, not to a reply.")
        return parent


class MessageSerializer(serializers.ModelSerializer):
    """`mine` comes from the server, on purpose.

    `thread.html` says so in its own comment: working it out in the template by
    comparing usernames breaks the day somebody changes their display name.
    """

    mine = serializers.SerializerMethodField()
    sent_at = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "mine", "text", "sent_at"]

    def get_mine(self, message) -> bool:
        request = self.context.get("request")
        return bool(request and message.sender_id == request.user.pk)

    def get_sent_at(self, message) -> str:
        return date_filter(message.sent_at, "H:i")
