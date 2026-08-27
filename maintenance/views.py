from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import OwnerScopedQuerysetMixin
from .models import MaintenanceRequest
from .serializers import MaintenanceRequestSerializer


class MaintenanceRequestViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MaintenanceRequest.objects.select_related('property', 'assigned_to').order_by('-reported_at')
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'property__owner'

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.request.query_params.get('property') or self.request.query_params.get('apartment')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset

    def perform_create(self, serializer):
        item = serializer.save()
        from integrations.views import trigger_automation

        trigger_automation('MAINTENANCE_CREATED', {
            'maintenance_id': item.id,
            'property': item.property.title,
            'title': item.title,
            'description': item.description,
            'priority': item.priority,
            'status': item.status,
            'assigned_to': str(item.assigned_to) if item.assigned_to else '',
        })

    def perform_update(self, serializer):
        item = serializer.save()
        from integrations.views import trigger_automation

        trigger_automation('MAINTENANCE_UPDATED', {
            'maintenance_id': item.id,
            'property': item.property.title,
            'title': item.title,
            'priority': item.priority,
            'status': item.status,
            'assigned_to': str(item.assigned_to) if item.assigned_to else '',
        })
