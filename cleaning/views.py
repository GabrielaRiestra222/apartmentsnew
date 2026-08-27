from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import OwnerScopedQuerysetMixin
from .models import CleaningTask
from .serializers import CleaningTaskSerializer


class CleaningTaskViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CleaningTask.objects.select_related('property', 'booking').order_by('scheduled_date')
    serializer_class = CleaningTaskSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'property__owner'

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.request.query_params.get('property') or self.request.query_params.get('apartment')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset
