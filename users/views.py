from rest_framework import viewsets

from common.permissions import IsAdminRole
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Gestión de cuentas y roles, reservada a administradores."""

    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
