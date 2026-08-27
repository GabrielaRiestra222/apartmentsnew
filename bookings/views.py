from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import OwnerScopedQuerysetMixin
from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Booking.objects
        .select_related('apartment', 'client', 'agency')
        .prefetch_related('payments', 'apartment__images')
        .order_by('-check_in')
    )
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'apartment__owner'

    def get_queryset(self):
        queryset = super().get_queryset()
        property_id = self.request.query_params.get('property') or self.request.query_params.get('apartment')
        if property_id:
            queryset = queryset.filter(apartment_id=property_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='return-deposit')
    def return_deposit(self, request, pk=None):
        """Mark this booking's security deposit as returned to the guest."""
        booking = self.get_object()
        booking.deposit_returned = True
        booking.deposit_returned_at = timezone.now()
        booking.save(update_fields=['deposit_returned', 'deposit_returned_at'])
        return Response(self.get_serializer(booking).data)
