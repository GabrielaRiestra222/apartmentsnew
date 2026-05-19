from django.db import models


class BookingSource(models.Model):

    SOURCE_TYPE = (
        ('AGENCY', 'Agency'),
        ('PORTAL', 'Portal'),
        ('DIRECT', 'Direct'),
    )

    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE)

    default_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
