from django.db import models


class Agency(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'
        ordering = ['name']

    def __str__(self):
        return self.name
