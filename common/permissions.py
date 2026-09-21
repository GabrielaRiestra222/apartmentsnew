from common.tenancy import default_organization
from rest_framework.exceptions import PermissionDenied
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
    """Solo superusuarios y rol ADMIN; para gestionar cuentas y permisos."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role == 'ADMIN'))


class IsStaffRole(BasePermission):
    """Superusuarios, ADMIN y MANAGER. Los propietarios (OWNER) quedan fuera."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and (user.is_superuser or user.role in ('ADMIN', 'MANAGER'))
        )


def sees_all_organizations(user):
    # Un ADMIN sin organización asignada gestiona toda la plataforma.
    return user.is_superuser or (user.role == 'ADMIN' and user.organization_id is None)


def _resolve(obj, path):
    for part in path.split('.'):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


class OwnerScopedQuerysetMixin:
    """
    Limita el queryset al alcance del usuario:
    - `organization_lookup`: ruta ORM hasta la organización (p. ej. 'apartment__organization').
      Cada usuario solo ve datos de su organización.
    - `owner_lookup`: ruta ORM hasta Property.owner. Un OWNER solo ve sus apartamentos.

    Al crear o editar, `organization_check` (p. ej. 'property.organization_id')
    impide enlazar el registro con datos de otra organización.
    """

    owner_lookup = None
    organization_lookup = None
    organization_check = None
    # True para modelos con campo `organization` propio (clientes, agencias...).
    assign_organization = False

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated or sees_all_organizations(user):
            return queryset

        if self.organization_lookup:
            queryset = queryset.filter(**{self.organization_lookup: user.organization_id})

        if getattr(user, 'role', None) == 'OWNER' and self.owner_lookup:
            queryset = queryset.filter(**{self.owner_lookup: user})

        return queryset

    def _check_organization(self, serializer):
        user = self.request.user
        if not self.organization_check or sees_all_organizations(user):
            return
        related = serializer.validated_data.get(self.organization_check.split('.')[0])
        if related is None:
            return
        path = self.organization_check.split('.', 1)[1]
        if _resolve(related, path) != user.organization_id:
            raise PermissionDenied('No tienes acceso a ese recurso.')

    def creation_organization(self):
        return self.request.user.organization or default_organization()

    def perform_create(self, serializer):
        self._check_organization(serializer)
        if self.assign_organization:
            serializer.save(organization=self.creation_organization())
            return
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._check_organization(serializer)
        super().perform_update(serializer)
