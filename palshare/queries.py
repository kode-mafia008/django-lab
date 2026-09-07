"""Visibility rules, written once.

Day 10 ended with the same rule written twice — once in a DRF `get_queryset`
and once in a plain view — because a permission class protects a DRF view and
nothing else. This module is the fix: both consumers import from here, so
"what may this person see" has exactly one definition.

Nothing in here takes a `request`. Every function takes a `user` and plain
arguments, which is what lets the API view and the page view call the same
function instead of each growing its own copy of the rule.
"""

from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Q

from .models import Comment, CommentLike, Conversation, Follow, Like, Post, Save, Share


def visible_posts(user):
    """Posts `user` may see: their own, everything public, and followers-only
    posts by people they follow."""
    followed = Follow.objects.filter(follower=user).values("following")
    return (
        Post.objects
        .select_related("author")
        .prefetch_related("media")
        .annotate(
            liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
            saved=Exists(Save.objects.filter(user=user, post=OuterRef("pk"))),
            shared=Exists(Share.objects.filter(user=user, post=OuterRef("pk"))),
        )
        .filter(Q(author=user) | Q(followers_only=False) | Q(author__in=followed))
    )


def saved_posts(user):
    """The saved page is the feed, filtered to rows this person starred.

    Still built on `visible_posts`: unfollowing somebody should hide their
    followers-only posts everywhere, including from a list you saved them to.
    """
    return visible_posts(user).filter(saves__user=user)


def may_see_posts(viewer, owner):
    """A private account shows its posts to itself and its followers, nobody else."""
    if viewer == owner:
        return True
    if not owner.profile.is_private:
        return True
    return Follow.objects.filter(follower=viewer, following=owner).exists()


def people(viewer, queryset=None):
    """Users, annotated with whether `viewer` already follows each one.

    The annotation is the same trick `visible_posts` plays with `liked`: a
    per-viewer fact computed for the whole page in the query that fetches it,
    rather than one query per row inside a serializer.
    """
    queryset = User.objects.all() if queryset is None else queryset
    # `select_related`, because every row serializer reads `profile.bio`, and a
    # OneToOne followed per row is the same N+1 as any other — it is just
    # spelled as an attribute access instead of a query.
    return queryset.select_related("profile").annotate(
        is_following=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("pk"))),
    )


def suggestions_for(user, limit=3):
    """The right rail: people this person is not following yet, and not themselves."""
    followed = Follow.objects.filter(follower=user).values("following")
    return people(user, User.objects.exclude(pk=user.pk).exclude(pk__in=followed))[:limit]


def conversations_for(me):
    """Every conversation `me` is in, newest first, with the two facts the
    inbox badge needs: the other participant and how many unread messages.

    `prefetch_related` then counting in Python, rather than a `.filter()` per
    row: the prefetch is two queries for the whole page, and re-filtering a
    prefetched relation throws the cache away and goes back to the database.
    """
    rows = []
    for conversation in (Conversation.objects
                         .filter(participants=me)
                         .prefetch_related("participants", "messages__sender")):
        others = [p for p in conversation.participants.all() if p.pk != me.pk]
        messages = list(conversation.messages.all())
        rows.append({
            "conversation": conversation,
            "other": others[0] if others else me,
            "last": messages[-1] if messages else None,
            "unread": sum(1 for m in messages
                          if m.read_at is None and m.sender_id != me.pk),
        })
    return rows


def search(user, q):
    q = q.strip()
    if len(q) < 2:
        # Two characters is not a search, it is a table scan. The page has an
        # empty state for exactly this.
        return {"query": q, "people": [], "posts": []}
    return {
        "query": q,
        "people": people(user, User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q)
        ))[:10],
        # `visible_posts`, not `Post.objects`: search is the classic way private
        # data leaks, because the detail page checks permissions and the search
        # does not.
        "posts": visible_posts(user).filter(text__icontains=q)[:20],
    }


def visible_comments(user, post):
    """A post's top-level comments, with the viewer's own likes annotated.

    Same `Exists()` trick as the feed: `liked` is a per-viewer fact, so it is
    computed for the whole thread in the query that fetches it rather than one
    query per comment.
    """
    return (Comment.objects
            .filter(post=post, parent__isnull=True)
            .select_related("author", "author__profile")
            .prefetch_related("replies__author", "replies__author__profile")
            .annotate(liked=Exists(CommentLike.objects.filter(user=user,
                                                              comment=OuterRef("pk")))))
