from django.db import models


class ChannelConnection(models.Model):
    CHANNEL_CHOICES = [
        ('AIRBNB', 'Airbnb'),
        ('BOOKING', 'Booking.com'),
        ('VRBO', 'Vrbo'),
        ('EXPEDIA', 'Expedia'),
        ('TRIPADVISOR', 'Tripadvisor'),
        ('AGODA', 'Agoda'),
        ('GOOGLE_VR', 'Google Vacation Rentals'),
        ('DIRECT', 'Web directa'),
        ('ICAL', 'iCal'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONNECTED', 'Connected'),
        ('ERROR', 'Error'),
        ('PAUSED', 'Paused'),
    ]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='channel_connections')
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES)
    external_listing_id = models.CharField(max_length=255, blank=True)
    ical_import_url = models.URLField(blank=True)
    ical_export_token = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    content_sync_enabled = models.BooleanField(default=True)
    rates_sync_enabled = models.BooleanField(default=True)
    availability_sync_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('property', 'channel', 'external_listing_id')
        ordering = ['property', 'channel']


class SeasonalRate(models.Model):
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='seasonal_rates')
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    min_nights = models.PositiveIntegerField(default=1)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_date']


class InboxMessage(models.Model):
    CHANNEL_CHOICES = ChannelConnection.CHANNEL_CHOICES + [('WHATSAPP', 'WhatsApp'), ('TELEGRAM', 'Telegram'), ('EMAIL', 'Email')]
    DIRECTION_CHOICES = [('INBOUND', 'Inbound'), ('OUTBOUND', 'Outbound')]

    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    sender = models.CharField(max_length=255, blank=True)
    recipient = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    external_id = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class GuestCheckIn(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='guest_checkin')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    document_id = models.CharField(max_length=80, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    signature_data = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SmartLockCode(models.Model):
    PROVIDER_CHOICES = [('NUKI', 'Nuki'), ('YALE', 'Yale'), ('REMOTELOCK', 'RemoteLock'), ('TTLOCK', 'TTLock'), ('MANUAL', 'Manual')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('ACTIVE', 'Active'), ('REVOKED', 'Revoked'), ('ERROR', 'Error')]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='smart_lock_codes')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='smart_lock_codes')
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='MANUAL')
    code = models.CharField(max_length=40)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    external_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DynamicPricingRule(models.Model):
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='pricing_rules')
    name = models.CharField(max_length=120)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    weekend_markup_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    occupancy_markup_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_minute_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    provider = models.CharField(max_length=40, default='BASIC')
    is_active = models.BooleanField(default=True)


class PaymentIntent(models.Model):
    PROVIDER_CHOICES = [('STRIPE', 'Stripe'), ('REDSYS', 'Redsys'), ('MERCADOPAGO', 'MercadoPago'), ('MANUAL', 'Manual')]
    STATUS_CHOICES = [('CREATED', 'Created'), ('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed'), ('CANCELLED', 'Cancelled')]

    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='payment_intents')
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='MANUAL')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
    checkout_url = models.URLField(blank=True)
    external_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationWebhook(models.Model):
    EVENT_CHOICES = [
        ('CLIENT_CREATED', 'Client created'),
        ('BOOKING_CREATED', 'Booking created'),
        ('MAINTENANCE_CREATED', 'Maintenance created'),
        ('MAINTENANCE_UPDATED', 'Maintenance updated'),
        ('CHECKIN_COMPLETED', 'Check-in completed'),
    ]
    TARGET_CHOICES = [('N8N', 'n8n'), ('WHATSAPP', 'WhatsApp'), ('TELEGRAM', 'Telegram'), ('CUSTOM', 'Custom')]

    name = models.CharField(max_length=120)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES)
    target = models.CharField(max_length=30, choices=TARGET_CHOICES, default='N8N')
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    secret = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationEvent(models.Model):
    webhook = models.ForeignKey(AutomationWebhook, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event = models.CharField(max_length=40)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
