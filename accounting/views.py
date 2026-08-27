from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import OwnerScopedQuerysetMixin
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related('property', 'booking').order_by('-date')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'property__owner'
