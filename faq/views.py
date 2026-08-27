from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Prefetch
from .models import FAQCategory, FAQ
from .serializers import FAQCategorySerializer, FAQSerializer


class FAQCategoryViewSet(viewsets.ModelViewSet):
    queryset = FAQCategory.objects.prefetch_related('faqs').order_by('order')
    serializer_class = FAQCategorySerializer
    permission_classes = [IsAuthenticated]


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.select_related('category').order_by('order')
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]


class PublicFAQViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only endpoint — returns only published FAQs grouped by category."""
    queryset = FAQCategory.objects.prefetch_related('faqs').order_by('order')
    serializer_class = FAQCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return FAQCategory.objects.prefetch_related(
            Prefetch('faqs', queryset=FAQ.objects.filter(is_published=True).order_by('order'))
        ).filter(faqs__is_published=True).distinct().order_by('order')
