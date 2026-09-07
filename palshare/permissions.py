from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Day 10's rule, applied to every object in this app.

    Authentication says who you are; this says which rows you may change.
    Anything else is Broken Object Level Authorization, which is number one on
    the OWASP API list for a reason.
    """

    message = "You can only change things you created."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id is not None and obj.author_id == request.user.id
