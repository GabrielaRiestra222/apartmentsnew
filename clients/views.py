from rest_framework import viewsets
from common.permissions import OwnerScopedQuerysetMixin
from rest_framework.permissions import IsAuthenticated
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all().order_by('last_name', 'first_name')
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    organization_lookup = 'organization'

    def perform_create(self, serializer):
        client = serializer.save(organization=self.creation_organization())
        from integrations.views import trigger_automation

        trigger_automation('CLIENT_CREATED', {
            'client_id': client.id,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'email': client.email,
            'phone': client.phone,
        })
