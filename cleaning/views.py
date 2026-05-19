from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CleaningTask
from .serializers import CleaningTaskSerializer


class CleaningTaskViewSet(viewsets.ModelViewSet):
    queryset = CleaningTask.objects.select_related('property', 'booking').order_by('scheduled_date')
    serializer_class = CleaningTaskSerializer
    permission_classes = [IsAuthenticated]
