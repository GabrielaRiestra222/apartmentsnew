from rest_framework import viewsets
from common.permissions import OwnerScopedQuerysetMixin
from rest_framework.permissions import IsAuthenticated
from .models import Agency
from .serializers import AgencySerializer


class AgencyViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Agency.objects.all().order_by('name')
    serializer_class = AgencySerializer
    permission_classes = [IsAuthenticated]
    organization_lookup = 'organization'
    assign_organization = True
