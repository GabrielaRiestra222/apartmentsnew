from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


class Booking(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )

    # 🔹 NO usamos "property" como nombre de campo
    apartment = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        related_name='bookings',
        null=True,
        blank=True
    )

    client_name = models.CharField(max_length=255, blank=True)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=20, blank=True)

    check_in = models.DateField()
    check_out = models.DateField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    source = models.ForeignKey(
        'sources.BookingSource',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='bookings',
    )
    agency = models.ForeignKey(
        'agencies.Agency',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='bookings',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    notes = models.TextField(blank=True)
    num_guests = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    # -----------------------------
    # VALIDACIONES
    # -----------------------------
    def clean(self):

        # Check-out posterior
        if self.check_out <= self.check_in:
            raise ValidationError("Check-out must be after check-in.")

        # Evitar solapamientos
        overlapping = Booking.objects.filter(
            apartment=self.apartment,
            status__in=['PENDING', 'CONFIRMED'],
            check_in__lt=self.check_out,
            check_out__gt=self.check_in
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This apartment is already booked for these dates.")

    # -----------------------------
    # PROPIEDADES FINANCIERAS
    # -----------------------------
    @property
    def total_paid(self):
        return sum(
            (payment.amount_paid for payment in self.payments.all()),
            Decimal('0.00')
        )

    @property
    def remaining_balance(self):
        return self.total_price - self.total_paid

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.apartment} | {self.check_in} → {self.check_out}"
