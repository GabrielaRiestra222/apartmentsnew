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


class IsAdminRole(BasePermission):
    """
    Restricts access to superusers or users with role='ADMIN'. Used for
    endpoints that manage other users' accounts and permissions.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role == 'ADMIN'))


class OwnerScopedQuerysetMixin:
    """
    Mixin for viewsets whose queryset should be narrowed to a single
    property owner's portfolio when the logged-in user has role='OWNER'.

    Set `owner_lookup` on the viewset to the ORM path from the model to
    the Property.owner field, e.g. 'owner', 'apartment__owner',
    'property__owner', 'booking__apartment__owner'.

    Superusers and ADMIN/MANAGER roles see everything, unaffected.
    """

    owner_lookup = None

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated or user.is_superuser:
            return queryset

        if getattr(user, 'role', None) == 'OWNER' and self.owner_lookup:
            return queryset.filter(**{self.owner_lookup: user})

        return queryset
