from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import BookingSource
from .serializers import BookingSourceSerializer


class BookingSourceViewSet(viewsets.ModelViewSet):
    queryset = BookingSource.objects.all().order_by('name')
    serializer_class = BookingSourceSerializer
    permission_classes = [IsAuthenticated]
