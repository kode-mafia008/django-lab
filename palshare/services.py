"""The writes, written once — the mirror of `queries.py`.

`queries.py` answers "what may this person see". This answers "what happens
when they tap it", and for the same reason: the page and the API both need
these rules, and a rule written twice is a rule that will disagree with itself
by hour nine.

Every function here is **idempotent** and returns the resulting state, never
the change. Liking twice is not an error, it is a no-op that returns `True`,
because a double tap on a slow connection is not a mistake the user should
hear about. The endpoint returns the new state so the UI never has to guess.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.db.models import F

from .models import (Comment, CommentLike, Conversation, Follow, Like, Media, Post,
                     Reaction, Save, Share)
from .validators import validate_upload, validate_uploads


def _bump(owner, field, by):
    """Move a counter cache, without letting it go negative.

    `F()` rather than `owner.field + 1`: two people liking at the same moment
    both read the same number and both write it back, and one of the likes
    disappears. The database can add; let it.
    """
    queryset = type(owner).objects.filter(pk=owner.pk)
    if by < 0:
        # A counter that has already drifted to zero must not wrap around into
        # four billion, which is what a PositiveIntegerField does on underflow.
        queryset = queryset.filter(**{f"{field}__gt": 0})
    queryset.update(**{field: F(field) + by})


def _add(model, owner, field, **lookup):
    """Create the row unless the unique constraint says it is already there."""
    try:
        # The savepoint is load-bearing: a constraint violation marks the whole
        # surrounding transaction as broken, so without one to roll back to,
        # catching IntegrityError buys nothing and the next query in the
        # request dies with TransactionManagementError.
        with transaction.atomic():
            model.objects.create(**lookup)
    except IntegrityError:
        return False  # the unique constraint did its job
    _bump(owner, field, 1)
    return True


def _remove(model, owner, field, **lookup):
    deleted, _ = model.objects.filter(**lookup).delete()
    if deleted:
        _bump(owner, field, -1)
    return bool(deleted)


def set_like(user, post, on):
    if on:
        _add(Like, post, "like_count", user=user, post=post)
    else:
        _remove(Like, post, "like_count", user=user, post=post)
    return on


def set_save(user, post, on):
    """No counter to move: nothing in the UI renders "saved by 12 people",
    so a save is a row and nothing else."""
    if on:
        try:
            with transaction.atomic():  # see `_add` for why the savepoint matters
                Save.objects.create(user=user, post=post)
        except IntegrityError:
            pass
    else:
        Save.objects.filter(user=user, post=post).delete()
    return on


def set_share(user, post, on):
    if on:
        _add(Share, post, "share_count", user=user, post=post)
    else:
        _remove(Share, post, "share_count", user=user, post=post)
    return on


def set_comment_like(user, comment, on):
    if on:
        _add(CommentLike, comment, "like_count", user=user, comment=comment)
    else:
        _remove(CommentLike, comment, "like_count", user=user, comment=comment)
    return on


def set_follow(user, target, on):
    """`ValueError` rather than letting the CheckConstraint fire.

    The constraint is the guarantee and this is the error message: a database
    constraint firing is a 500, and a check first turns it into a sentence.
    You want both — the check for the ninety-nine per cent, the constraint for
    the race the check cannot see.
    """
    if user == target:
        raise ValueError("You cannot follow yourself.")
    if on:
        Follow.objects.get_or_create(follower=user, following=target)
    else:
        Follow.objects.filter(follower=user, following=target).delete()
    return on


def toggle_like(user, post):
    return set_like(user, post, not Like.objects.filter(user=user, post=post).exists())


def toggle_save(user, post):
    return set_save(user, post, not Save.objects.filter(user=user, post=post).exists())


def toggle_share(user, post):
    return set_share(user, post, not Share.objects.filter(user=user, post=post).exists())


def toggle_comment_like(user, comment):
    return set_comment_like(
        user, comment, not CommentLike.objects.filter(user=user, comment=comment).exists())


def toggle_follow(user, target):
    return set_follow(user, target,
                      not Follow.objects.filter(follower=user, following=target).exists())


def add_comment(user, post, text, parent=None):
    """One place that knows a comment bumps a counter and a reply cannot nest.

    The model allows any depth — a CheckConstraint cannot walk a tree — so the
    rule that replies go one level deep lives here and in the serializer.
    """
    if parent is not None and parent.parent_id is not None:
        parent = parent.parent  # a reply to a reply attaches to its top-level comment
    comment = Comment.objects.create(post=post, author=user, text=text, parent=parent)
    _bump(post, "comment_count", 1)
    return comment


def conversation_with(me, other):
    """The one conversation between two people, created on first message.

    Two `filter()` calls, not one with two participants: a single filter on a
    ManyToMany matches rows with *either* participant. Chaining them means
    "has me AND has other".
    """
    existing = (Conversation.objects
                .filter(participants=me)
                .filter(participants=other)
                .first())
    if existing:
        return existing
    conversation = Conversation.objects.create()
    conversation.participants.add(me, other)
    return conversation


def attach_media(post, uploads):
    """Store uploaded files against a post and return the new `Media` rows.

    Every file is validated before the first one is written, so a four-file
    post with one bad file stores nothing — a post that half-uploaded is worse
    to explain than one that did not upload at all.

    Raises `django.core.exceptions.ValidationError`. Callers translate it:
    the view turns it into `messages.error`, the serializer re-raises it as
    DRF's ValidationError so the API answers 400 rather than 500.

    One thing this cannot give you: the files are written to disk by
    `FileField.pre_save`, and a rolled-back transaction does not unwrite them.
    A failure after this point leaves bytes in MEDIA_ROOT with no row pointing
    at them. That is the normal Django trade-off, and the reason validation
    happens first rather than being discovered halfway through.
    """
    uploads = list(uploads)
    if not uploads:
        return []
    checked = validate_uploads(uploads, existing=post.media.count())
    return [Media.objects.create(post=post, file=upload, kind=kind)
            for upload, kind in checked]


def set_reaction(user, post, emoji):
    """Set, change or clear this person's one reaction to a post.

    Three behaviours in one function because they are one behaviour from the
    user's side: pressing an emoji you already picked takes it back, pressing a
    different one moves your reaction, and `emoji=None` clears it. Everything
    returns the resulting emoji, or None, so the caller never has to re-read.

    `update_or_create` rather than delete-then-create: the unique constraint is
    on (user, post), and a delete/create pair is a window in which a double tap
    creates two rows.
    """
    valid = {value for value, _ in Reaction.EMOJI}
    if emoji is not None and emoji not in valid:
        # A fixed palette that only the template enforces is not a fixed
        # palette — this endpoint takes whatever a caller posts to it.
        raise ValidationError("That is not one of the reactions.")

    current = Reaction.objects.filter(user=user, post=post).first()
    if emoji is None or (current and current.emoji == emoji):
        Reaction.objects.filter(user=user, post=post).delete()
        return None
    Reaction.objects.update_or_create(user=user, post=post, defaults={"emoji": emoji})
    return emoji


def reaction_summary(post, user):
    """The whole palette with counts, for one post.

    Every emoji is returned, including the ones nobody picked, so the bar under
    a post has the same five buttons whether it has a thousand reactions or
    none. Reads the `reactions` prefetch rather than querying: called once per
    row of a feed, a query here would be the N+1 the prefetch exists to avoid.
    """
    rows = list(post.reactions.all())
    mine = next((r.emoji for r in rows if r.user_id == getattr(user, "pk", None)), None)
    counts = {}
    for reaction in rows:
        counts[reaction.emoji] = counts.get(reaction.emoji, 0) + 1
    return [{"emoji": emoji, "label": label, "count": counts.get(emoji, 0),
             "mine": mine == emoji}
            for emoji, label in Reaction.EMOJI]


def edit_message(user, message, text):
    """Change the text of a message you sent.

    Three rules, and the first two are the whole feature: you may only edit
    your own, and you may not edit one you already unsent. The third is that an
    edit is stamped, because a message that can change silently is a message
    the other person cannot trust.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only edit messages you sent.")
    if message.is_deleted:
        raise ValidationError("That message was unsent.")
    text = (text or "").strip()
    if not text:
        # Emptying a message is unsending it, and unsending has its own
        # function that clears the text properly and says so in the thread.
        raise ValidationError("An edited message still needs some text.")
    message.text = text
    message.edited_at = timezone.now()
    message.save(update_fields=["text", "edited_at"])
    return message


def unsend_message(user, message):
    """Take back a message you sent.

    A soft delete that actually deletes the text. The row survives so the
    thread keeps its order and the other person sees "this message was
    unsent" rather than a conversation that quietly reads differently than
    they remember — but the words are gone from the database, because an
    unsent message the server still stores is not unsent.

    Idempotent, like every other write in this module: unsending twice is the
    same as unsending once, not an error.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only unsend messages you sent.")
    if message.is_deleted:
        return message
    message.text = ""
    message.deleted_at = timezone.now()
    message.save(update_fields=["text", "deleted_at"])
    return message


def set_avatar(profile, upload):
    """Store a profile picture, through the same allowlist as post media.

    Deliberately the same `validate_upload`: a second, looser rule for avatars
    is how the one place that checks uploads becomes the one place that used
    to. Videos are rejected here because a moving avatar is not a feature
    anybody asked for.
    """
    kind = validate_upload(upload)
    if kind != "image":
        raise ValidationError("A profile picture has to be an image.")
    # The old file is not deleted: it may be the default, and unlinking a file
    # a database row still points at is how you get a broken image everywhere
    # it was cached. Cleaning up storage is its own job, with its own
    # management command.
    profile.avatar = upload
    profile.save(update_fields=["avatar"])
    return profile
