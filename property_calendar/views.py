from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CalendarBlock
from .serializers import CalendarBlockSerializer


class CalendarBlockViewSet(viewsets.ModelViewSet):
    queryset = CalendarBlock.objects.select_related('property', 'booking').order_by('start_date')
    serializer_class = CalendarBlockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.request.query_params.get('property') or self.request.query_params.get('apartment')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset
