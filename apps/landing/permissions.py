from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read: allow any request
    - Write: only allow admin users
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsAdminOnly(permissions.BasePermission):
    """
    Custom permission:
    - Only allow admin users
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission:
    - Only allow verified users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Allow staff regardless of verification
        if request.user.is_staff:
            return True
        # Check if user is verified
        return getattr(request.user, 'is_verified', False)