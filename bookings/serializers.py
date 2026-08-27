from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from decimal import Decimal
from .models import Booking
from payments.serializers import BookingPaymentSerializer


class BookingSerializer(serializers.ModelSerializer):
    total_paid = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    remaining_balance = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    payments = BookingPaymentSerializer(many=True, read_only=True)
    pending_payments_count = serializers.SerializerMethodField()
    price_per_night = serializers.SerializerMethodField()

    # Derived read-only fields
    apartment_title = serializers.CharField(source='apartment.title', read_only=True)
    apartment_image = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    agency_name = serializers.CharField(source='agency.name', read_only=True, default=None)

    def get_apartment_image(self, obj):
        if not obj.apartment_id:
            return None
        images = list(obj.apartment.images.all())
        if not images:
            return None
        main = next((img for img in images if img.is_main), images[0])
        return main.image or None

    def get_client_name(self, obj):
        """Return name from related Client if linked, otherwise from the stored field."""
        if obj.client_id:
            first = getattr(obj.client, 'first_name', '') or ''
            last = getattr(obj.client, 'last_name', '') or ''
            full = f"{first} {last}".strip()
            if full:
                return full
        return obj.client_name or ''

    def get_pending_payments_count(self, obj):
        return obj.payments.filter(status='PENDING').count()

    def get_price_per_night(self, obj):
        nights = max((obj.check_out - obj.check_in).days, 1)
        return (obj.total_price / Decimal(nights)).quantize(Decimal('0.01'))

    class Meta:
        model = Booking
        fields = (
            'id', 'apartment', 'apartment_title', 'apartment_image',
            'client', 'client_id', 'client_name', 'client_email', 'client_phone',
            'source', 'agency', 'agency_name',
            'check_in', 'check_out', 'total_price', 'status',
            'notes', 'num_guests', 'created_at',
            'total_paid', 'remaining_balance', 'payments',
            'pending_payments_count', 'price_per_night',
            'deposit_amount', 'deposit_returned', 'deposit_returned_at',
        )
        read_only_fields = (
            'created_at', 'client_id', 'apartment_title', 'apartment_image', 'agency_name',
            'pending_payments_count', 'price_per_night',
            'deposit_returned', 'deposit_returned_at',
        )

    def validate(self, attrs):
        # Build a temporary instance to run model-level clean()
        instance = self.instance
        booking = Booking(
            apartment=attrs.get('apartment', getattr(instance, 'apartment', None)),
            client=attrs.get('client', getattr(instance, 'client', None)),
            source=attrs.get('source', getattr(instance, 'source', None)),
            agency=attrs.get('agency', getattr(instance, 'agency', None)),
            check_in=attrs.get('check_in', getattr(instance, 'check_in', None)),
            check_out=attrs.get('check_out', getattr(instance, 'check_out', None)),
            total_price=attrs.get('total_price', getattr(instance, 'total_price', None)),
            status=attrs.get('status', getattr(instance, 'status', 'PENDING')),
            notes=attrs.get('notes', getattr(instance, 'notes', '')),
            num_guests=attrs.get('num_guests', getattr(instance, 'num_guests', 1)),
        )
        if instance:
            booking.id = instance.id

        try:
            booking.clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        return attrs
