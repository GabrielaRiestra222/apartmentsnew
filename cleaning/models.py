from django.db import models


class CleaningTask(models.Model):
    STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='cleaning_tasks',
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cleaning_tasks',
    )
    assigned_to = models.ForeignKey(
        'team.TeamMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cleaning_tasks',
    )
    scheduled_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    notes = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cleaning Task'
        verbose_name_plural = 'Cleaning Tasks'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"Cleaning {self.property} on {self.scheduled_date}"
