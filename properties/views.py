import uuid
from django.core.files.storage import default_storage
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from rest_framework.permissions import SAFE_METHODS

from common.permissions import IsStaffRole, OwnerScopedQuerysetMixin
from .models import Property, Amenity, PropertyImage
from .serializers import PropertySerializer, PublicPropertySerializer, AmenitySerializer, PropertyImageSerializer


class PropertyViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Property.objects
        .select_related('organization', 'owner')
        .prefetch_related('bookings', 'images', 'amenities')
        .order_by('title')
    )
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'owner'
    organization_lookup = 'organization'

    def perform_create(self, serializer):
        # Los administradores sin organización usan la primera disponible.
        organization = self.request.user.organization
        if organization is None:
            from organizations.models import Organization
            organization = Organization.objects.order_by('id').first()
        serializer.save(organization=organization)

    @action(detail=False, methods=['post'], url_path='upload-image', permission_classes=[IsAuthenticated])
    def upload_image(self, request):
        """Sube una imagen y devuelve su URL pública."""
        return handle_property_image_upload(request)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def calendar(self, request, pk=None):
        """Bloqueos de calendario de esta propiedad."""
        from property_calendar.serializers import CalendarBlockSerializer
        prop = self.get_object()
        blocks = prop.calendar_blocks.select_related('booking').order_by('start_date')
        serializer = CalendarBlockSerializer(blocks, many=True)
        return Response(serializer.data)


class PublicPropertyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """Catálogo público: solo lectura y solo propiedades publicadas."""
    queryset = (
        Property.objects
        .filter(is_published=True, is_active=True)
        .prefetch_related('images', 'amenities')
        .order_by('title')
    )
    serializer_class = PublicPropertySerializer
    permission_classes = [AllowAny]


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all().order_by('name')
    serializer_class = AmenitySerializer

    def get_permissions(self):
        # Los amenities son compartidos: cualquiera con sesión los lee, solo el staff los edita.
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsStaffRole()]


class PropertyImageViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PropertyImage.objects.select_related('property').order_by('property', 'order')
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]
    owner_lookup = 'property__owner'
    organization_lookup = 'property__organization'
    organization_check = 'property.organization_id'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_property_image(request):
    return handle_property_image_upload(request)


def handle_property_image_upload(request):
    file = request.FILES.get('image')
    property_id = request.data.get('property_id')

    if not file:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        return Response(
            {'error': 'Invalid file type. Only JPG, PNG, and WebP allowed.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if file.size > 10 * 1024 * 1024:
        return Response(
            {'error': 'File too large. Max size is 10MB.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    ext = file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    folder = f"properties/property_{property_id}" if property_id else "properties/temp"
    path = default_storage.save(f"{folder}/{filename}", file)
    url = default_storage.url(path)

    return Response({'url': url, 'filename': filename, 'path': path}, status=status.HTTP_201_CREATED)
