from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import OwnerScopedQuerysetMixin
from .models import BookingPayment
from .serializers import BookingPaymentSerializer


class BookingPaymentViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = BookingPayment.objects.select_related('booking', 'booking__apartment').order_by('-due_date')
    serializer_class = BookingPaymentSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'booking__apartment__owner'
    filterset_fields = ['status', 'booking']
