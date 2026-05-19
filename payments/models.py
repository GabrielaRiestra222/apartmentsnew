from django.db import models


class BookingPayment(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
    )

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    due_date = models.DateField()

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    payment_method = models.CharField(
        max_length=50,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    receipt_url = models.CharField(max_length=1000, blank=True)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Booking Payment'
        verbose_name_plural = 'Booking Payments'
        ordering = ['-due_date']

    def save(self, *args, **kwargs):
        if self.amount_paid >= self.amount_due:
            self.status = 'PAID'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for booking {self.booking.id}"
