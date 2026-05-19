from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = (
        Booking.objects
        .select_related('apartment', 'client', 'agency')
        .prefetch_related('payments')
        .order_by('-check_in')
    )
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
