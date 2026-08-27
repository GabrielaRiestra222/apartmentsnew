from rest_framework import viewsets

from common.permissions import IsAdminRole
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    User roster with role/permission management. Restricted to admins:
    this is where access levels (ADMIN/MANAGER/OWNER) get assigned, so it
    shouldn't be readable by the accounts it manages.
    """
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
