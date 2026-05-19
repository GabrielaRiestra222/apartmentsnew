from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import BookingPayment
from .serializers import BookingPaymentSerializer


class BookingPaymentViewSet(viewsets.ModelViewSet):
    queryset = BookingPayment.objects.select_related('booking').order_by('-due_date')
    serializer_class = BookingPaymentSerializer
    permission_classes = [IsAuthenticated]
