from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from bookings.models import Booking
from common.tenancy import default_organization
from bookings.serializers import BookingSerializer
from clients.models import Client
from payments.models import BookingPayment
from .models import (
    AutomationEvent,
    AutomationWebhook,
    ChannelConnection,
    DynamicPricingRule,
    GuestCheckIn,
    InboxMessage,
    PaymentIntent,
    SeasonalRate,
    SmartLockCode,
)


class ChannelConnectionSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = ChannelConnection
        fields = '__all__'


class SeasonalRateSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = SeasonalRate
        fields = '__all__'


class InboxMessageSerializer(serializers.ModelSerializer):
    booking_label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InboxMessage
        fields = '__all__'
        read_only_fields = ('organization',)

    def get_booking_label(self, obj):
        if not obj.booking:
            return ''
        return f'#{obj.booking_id} · {obj.booking.apartment.title}'


class GuestCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestCheckIn
        fields = '__all__'
        read_only_fields = ('completed_at',)

    def update(self, instance, validated_data):
        if validated_data.get('is_completed') and not instance.completed_at:
            validated_data['completed_at'] = timezone.now()
        return super().update(instance, validated_data)


class SmartLockCodeSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = SmartLockCode
        fields = '__all__'


class DynamicPricingRuleSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = DynamicPricingRule
        fields = '__all__'


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = '__all__'


class AutomationWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationWebhook
        fields = '__all__'


class AutomationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationEvent
        fields = '__all__'


class PublicBookingSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    guest_name = serializers.CharField(max_length=255)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=40, allow_blank=True, required=False)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1)

    DEPOSIT_PERCENT = Decimal('30.00')

    def validate(self, attrs):
        from properties.models import Property

        property_obj = Property.objects.filter(
            id=attrs['property_id'], is_published=True, is_active=True,
        ).first()
        if property_obj is None:
            raise serializers.ValidationError({'property_id': 'Property not available.'})

        nights = (attrs['check_out'] - attrs['check_in']).days
        if nights <= 0:
            raise serializers.ValidationError('Check-out must be after check-in.')
        if attrs['check_in'] < timezone.now().date():
            raise serializers.ValidationError({'check_in': 'Check-in cannot be in the past.'})
        if property_obj.min_nights and nights < property_obj.min_nights:
            raise serializers.ValidationError(f'Minimum stay is {property_obj.min_nights} nights.')
        if property_obj.max_guests and attrs['guests'] > property_obj.max_guests:
            raise serializers.ValidationError({'guests': f'Maximum {property_obj.max_guests} guests.'})

        # El precio lo fija el servidor; nunca se acepta el que envía el navegador.
        total = property_obj.price_per_night * nights + (property_obj.cleaning_fee or Decimal('0'))
        candidate = Booking(
            apartment=property_obj, check_in=attrs['check_in'],
            check_out=attrs['check_out'], total_price=total,
        )
        try:
            candidate.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        attrs['property'] = property_obj
        attrs['total'] = total
        return attrs

    def create(self, validated_data):
        property_obj = validated_data['property']
        name_parts = validated_data['guest_name'].split(' ', 1)
        client, _ = Client.objects.get_or_create(
            email=validated_data['guest_email'],
            organization=property_obj.organization,
            defaults={
                'first_name': name_parts[0],
                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                'phone': validated_data.get('guest_phone', ''),
            },
        )
        booking = Booking.objects.create(
            apartment=property_obj,
            client=client,
            client_name=validated_data['guest_name'],
            client_email=validated_data['guest_email'],
            client_phone=validated_data.get('guest_phone', ''),
            check_in=validated_data['check_in'],
            check_out=validated_data['check_out'],
            total_price=validated_data['total'],
            num_guests=validated_data['guests'],
            status='PENDING',
            notes='Reserva creada desde la web directa.',
        )
        BookingPayment.objects.create(
            booking=booking,
            amount_due=(validated_data['total'] * self.DEPOSIT_PERCENT / Decimal('100')).quantize(Decimal('0.01')),
            due_date=timezone.now().date(),
            notes='Señal de reserva directa',
        )
        return booking

    def to_representation(self, instance):
        return BookingSerializer(instance).data


class ContactRequestSerializer(serializers.Serializer):
    """Formulario de contacto de la landing."""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=40, allow_blank=True, required=False)
    guests = serializers.IntegerField(min_value=1, max_value=50, required=False)
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    message = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    def validate(self, attrs):
        check_in, check_out = attrs.get('check_in'), attrs.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({'check_out': 'Check-out must be after check-in.'})
        return attrs

    def create(self, data):
        lines = [f"Teléfono: {data['phone']}"] if data.get('phone') else []
        if data.get('check_in') and data.get('check_out'):
            lines.append(f"Fechas: {data['check_in']} → {data['check_out']}")
        if data.get('guests'):
            lines.append(f"Huéspedes: {data['guests']}")
        if data.get('message'):
            lines.append(data['message'])
        organization = default_organization()
        return InboxMessage.objects.create(
            organization=organization,
            channel='DIRECT',
            direction='INBOUND',
            sender=f"{data['name']} <{data['email']}>",
            client=Client.objects.filter(email=data['email'], organization=organization).first(),
            body='\n'.join(lines) or 'Solicitud de contacto sin mensaje.',
        )
