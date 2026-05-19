from django.db import models


class Transaction(models.Model):
    CATEGORY = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    property = models.ForeignKey(
        'properties.Property',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )
    category = models.CharField(max_length=10, choices=CATEGORY)
    subcategory = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    receipt_url = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date']

    def __str__(self):
        return f"{self.category} | {self.subcategory} | {self.amount}"
