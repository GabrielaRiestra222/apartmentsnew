from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrReadOnlyForProperties(BasePermission):
    """
    Allow public read-only access (GET, HEAD, OPTIONS).
    Require authentication for any write operation.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)
