"""Object-level permissions for the blog API.

A permission class answers two different questions, and DRF asks them at two
different moments:

* `has_permission(request, view)` — asked once, before the view runs, with no
  object in hand. "May this caller use this endpoint at all?"
* `has_object_permission(request, view, obj)` — asked per row, and *only* from
  `get_object()`. "May this caller touch this particular row?"

The second one is the one APIs forget, and forgetting it is the single most
common API vulnerability there is: authenticated user A edits user B's data by
changing a number in the URL.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Anyone who got past authentication may read; only the owner may write.

    `owner` is nullable, and `None == request.user` is False for every user —
    so a row written before ownership existed is read-only for everybody. That
    is deliberate. A permission check must fail closed.
    """

    message = "You can only change posts you created."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id is not None and obj.owner_id == request.user.id
