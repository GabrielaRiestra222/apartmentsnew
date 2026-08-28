from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from .models import CalendarBlock
from .serializers import CalendarBlockSerializer


class CalendarBlockPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 1000


class CalendarBlockViewSet(viewsets.ModelViewSet):
    queryset = CalendarBlock.objects.select_related('property', 'booking').order_by('start_date')
    serializer_class = CalendarBlockSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CalendarBlockPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.request.query_params.get('property') or self.request.query_params.get('apartment')
        date_from = self.request.query_params.get('date_from') or self.request.query_params.get('start')
        date_to = self.request.query_params.get('date_to') or self.request.query_params.get('end')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        if date_from:
            queryset = queryset.filter(end_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)
        return queryset
