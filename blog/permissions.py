from rest_framework import permissions

class IsOwnerReadonly(permissions.BasePermission):
    
    message = "you can only change posts you create"
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id is not None and obj.owner_id == request.user.id
    
    