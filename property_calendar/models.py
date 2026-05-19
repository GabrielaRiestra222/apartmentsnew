from django.db import models


class CalendarBlock(models.Model):
    REASON = [
        ('BOOKING', 'Booking'),
        ('MAINTENANCE', 'Maintenance'),
        ('CLEANING', 'Cleaning'),
        ('OWNER_USE', 'Owner Use'),
        ('BLOCKED', 'Blocked'),
    ]

    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='calendar_blocks',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=20, choices=REASON)
    booking = models.ForeignKey(
        'bookings.Booking',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='calendar_blocks',
    )
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Calendar Block'
        verbose_name_plural = 'Calendar Blocks'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.property} | {self.reason} | {self.start_date} → {self.end_date}"
