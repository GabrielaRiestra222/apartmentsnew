from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from bookings.models import Booking
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
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    deposit_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=Decimal('30.00'))

    def validate(self, attrs):
        if attrs['check_out'] <= attrs['check_in']:
            raise serializers.ValidationError('Check-out must be after check-in.')
        return attrs

    def create(self, validated_data):
        from properties.models import Property

        property_obj = Property.objects.get(id=validated_data['property_id'])
        name_parts = validated_data['guest_name'].split(' ', 1)
        client, _ = Client.objects.get_or_create(
            email=validated_data['guest_email'],
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
        deposit = validated_data['total'] * (validated_data['deposit_percent'] / Decimal('100'))
        BookingPayment.objects.create(
            booking=booking,
            amount_due=deposit,
            due_date=timezone.now().date(),
            notes='Señal de reserva directa',
        )
        return booking

    def to_representation(self, instance):
        return BookingSerializer(instance).data
