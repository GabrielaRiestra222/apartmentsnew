import hmac
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.throttles import ContactRateThrottle, PublicBookingRateThrottle
from common.permissions import IsStaffRole, OwnerScopedQuerysetMixin
from property_calendar.models import CalendarBlock
from properties.models import Property
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
from .serializers import (
    AutomationEventSerializer,
    AutomationWebhookSerializer,
    ChannelConnectionSerializer,
    ContactRequestSerializer,
    DynamicPricingRuleSerializer,
    GuestCheckInSerializer,
    InboxMessageSerializer,
    PaymentIntentSerializer,
    PublicBookingSerializer,
    SeasonalRateSerializer,
    SmartLockCodeSerializer,
)


class ChannelConnectionViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ChannelConnection.objects.select_related('property').order_by('property__title', 'channel')
    serializer_class = ChannelConnectionSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'property__organization'
    organization_check = 'property.organization_id'

    @action(detail=True, methods=['post'], url_path='sync-ical')
    def sync_ical(self, request, pk=None):
        connection = self.get_object()
        if not connection.ical_import_url:
            return Response({'detail': 'No iCal import URL configured.'}, status=status.HTTP_400_BAD_REQUEST)

        imported = import_ical_blocks(connection)
        connection.last_sync_at = timezone.now()
        connection.status = 'CONNECTED'
        connection.last_error = ''
        connection.save(update_fields=['last_sync_at', 'status', 'last_error'])
        return Response({'imported': imported})


class SeasonalRateViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = SeasonalRate.objects.select_related('property').order_by('start_date')
    serializer_class = SeasonalRateSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'property__organization'
    organization_check = 'property.organization_id'


class InboxMessageViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = InboxMessage.objects.select_related('booking', 'booking__apartment', 'client').order_by('-created_at')
    serializer_class = InboxMessageSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'organization'
    assign_organization = True


class GuestCheckInViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = GuestCheckIn.objects.select_related('booking').order_by('-created_at')
    serializer_class = GuestCheckInSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'booking__apartment__organization'
    organization_check = 'booking.apartment.organization_id'


class SmartLockCodeViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = SmartLockCode.objects.select_related('property', 'booking').order_by('-created_at')
    serializer_class = SmartLockCodeSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'property__organization'
    organization_check = 'property.organization_id'


class DynamicPricingRuleViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DynamicPricingRule.objects.select_related('property').order_by('property__title', 'name')
    serializer_class = DynamicPricingRuleSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'property__organization'
    organization_check = 'property.organization_id'


class PaymentIntentViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PaymentIntent.objects.select_related('booking').order_by('-created_at')
    serializer_class = PaymentIntentSerializer
    permission_classes = [IsStaffRole]
    organization_lookup = 'booking__apartment__organization'
    organization_check = 'booking.apartment.organization_id'

    def perform_create(self, serializer):
        self._check_organization(serializer)
        intent = serializer.save()
        if not intent.checkout_url:
            intent.checkout_url = f'{settings.CRM_BASE_URL}/payments?booking={intent.booking_id}&amount={intent.amount}'
            intent.save(update_fields=['checkout_url'])


class AutomationWebhookViewSet(viewsets.ModelViewSet):
    queryset = AutomationWebhook.objects.order_by('event', 'name')
    serializer_class = AutomationWebhookSerializer
    permission_classes = [IsStaffRole]

    @action(detail=True, methods=['post'], url_path='test')
    def test(self, request, pk=None):
        webhook = self.get_object()
        event = dispatch_webhook(webhook, {'test': True, 'source': 'dashboard'})
        return Response(AutomationEventSerializer(event).data)


class AutomationEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AutomationEvent.objects.select_related('webhook').order_by('-created_at')
    serializer_class = AutomationEventSerializer
    permission_classes = [IsStaffRole]


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PublicBookingRateThrottle])
def public_booking(request):
    serializer = PublicBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    booking = serializer.save()
    trigger_automation('BOOKING_CREATED', {
        'booking_id': booking.id,
        'property': booking.apartment.title,
        'guest_name': booking.client_name,
        'guest_email': booking.client_email,
        'check_in': str(booking.check_in),
        'check_out': str(booking.check_out),
        'total_price': str(booking.total_price),
    })
    return Response(serializer.to_representation(booking), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def property_ical_export(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_active=True)
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Apartments PMS//Booking Calendar//EN',
    ]
    bookings = property_obj.bookings.exclude(status='CANCELLED')
    for booking in bookings:
        lines.extend([
            'BEGIN:VEVENT',
            f'UID:booking-{booking.id}@apartments-pms',
            f'DTSTART;VALUE=DATE:{booking.check_in.strftime("%Y%m%d")}',
            f'DTEND;VALUE=DATE:{booking.check_out.strftime("%Y%m%d")}',
            'SUMMARY:Reserved',
            'END:VEVENT',
        ])
    blocks = property_obj.calendar_blocks.all()
    for block in blocks:
        lines.extend([
            'BEGIN:VEVENT',
            f'UID:block-{block.id}@apartments-pms',
            f'DTSTART;VALUE=DATE:{block.start_date.strftime("%Y%m%d")}',
            f'DTEND;VALUE=DATE:{block.end_date.strftime("%Y%m%d")}',
            f'SUMMARY:{block.reason}',
            'END:VEVENT',
        ])
    lines.append('END:VCALENDAR')
    return HttpResponse('\r\n'.join(lines), content_type='text/calendar')


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ContactRateThrottle])
def public_contact(request):
    serializer = ContactRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'ok': True}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def n8n_inbound(request):
    # Sin secreto configurado el endpoint queda cerrado; con él, solo entra quien lo conozca.
    expected = getattr(settings, 'N8N_INBOUND_SECRET', '')
    received = request.headers.get('X-Apartments-Secret', '')
    if not expected or not hmac.compare_digest(received, expected):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    event = request.data.get('event', 'CUSTOM')
    payload = request.data.get('payload', request.data)
    AutomationEvent.objects.create(event=event, payload=payload, status='RECEIVED')
    return Response({'ok': True})


def trigger_automation(event_name, payload):
    for webhook in AutomationWebhook.objects.filter(event=event_name, is_active=True):
        dispatch_webhook(webhook, payload)


def dispatch_webhook(webhook, payload):
    event = AutomationEvent.objects.create(webhook=webhook, event=webhook.event, payload=payload, status='PENDING')
    try:
        body = json.dumps(payload, default=str).encode('utf-8')
        request = Request(webhook.url, data=body, method='POST', headers={
            'Content-Type': 'application/json',
            **({'X-Apartments-Secret': webhook.secret} if webhook.secret else {}),
        })
        with urlopen(request, timeout=6) as response:
            event.response_status = response.status
            event.response_body = response.read().decode('utf-8', errors='ignore')[:2000]
            event.status = 'SENT'
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        event.status = 'ERROR'
        event.response_body = str(exc)
    event.save()
    return event


def import_ical_blocks(connection):
    request = Request(connection.ical_import_url, headers={'User-Agent': 'ApartmentsPMS/1.0'})
    with urlopen(request, timeout=12) as response:
        content = response.read().decode('utf-8', errors='ignore')

    imported = 0
    events = content.split('BEGIN:VEVENT')[1:]
    CalendarBlock.objects.filter(property=connection.property, reason='BOOKING', notes__icontains=f'iCal:{connection.id}').delete()
    for raw_event in events:
        start = extract_ical_date(raw_event, 'DTSTART')
        end = extract_ical_date(raw_event, 'DTEND')
        if not start or not end:
            continue
        CalendarBlock.objects.create(
            property=connection.property,
            start_date=start,
            end_date=end,
            reason='BOOKING',
            notes=f'iCal:{connection.id}',
        )
        imported += 1
    return imported


def extract_ical_date(raw_event, field):
    for line in raw_event.splitlines():
        if line.startswith(field):
            value = line.split(':', 1)[-1].strip()[:8]
            return timezone.datetime.strptime(value, '%Y%m%d').date()
    return None
