import base64
import uuid
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.permissions import IsAuthenticatedOrReadOnlyForProperties
from .models import Property, Amenity, PropertyImage
from .serializers import PropertySerializer, PublicPropertySerializer, AmenitySerializer, PropertyImageSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = (
        Property.objects
        .select_related('organization')
        .prefetch_related('bookings', 'images', 'amenities')
        .order_by('title')
    )
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForProperties]

    def perform_create(self, serializer):
        """Auto-assign organization from logged-in user."""
        print("=" * 50)
        print(f"DEBUG perform_create")
        print(f"User: {self.request.user}")
        print(f"User ID: {self.request.user.id}")
        print(f"Organization: {self.request.user.organization}")
        print(f"Validated data: {serializer.validated_data}")
        print("=" * 50)
        
        try:
            serializer.save(organization=self.request.user.organization)
            print("✅ Property created successfully")
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def perform_update(self, serializer):
        """Keep organization when updating."""
        serializer.save(organization=self.request.user.organization)

    @action(detail=False, methods=['post'], url_path='upload-image', permission_classes=[IsAuthenticated])
    def upload_image(self, request):
        """Upload an image file and return the public media URL."""
        return handle_property_image_upload(request)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def calendar(self, request, pk=None):
        """Return all calendar blocks for a specific property."""
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
    """Read-only, unauthenticated — only published properties."""
    queryset = (
        Property.objects
        .filter(is_published=True)
        .prefetch_related('images', 'amenities')
        .order_by('title')
    )
    serializer_class = PublicPropertySerializer
    permission_classes = [AllowAny]


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all().order_by('name')
    serializer_class = AmenitySerializer
    permission_classes = [IsAuthenticated]


class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.select_related('property').order_by('property', 'order')
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]


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

    encoded = base64.b64encode(file.read()).decode('ascii')
    data_url = f'data:{file.content_type};base64,{encoded}'

    ext = file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    return Response({'url': data_url, 'filename': filename, 'path': filename}, status=status.HTTP_201_CREATED)
