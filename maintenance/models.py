from django.db import models


class MaintenanceRequest(models.Model):
    PRIORITY = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    STATUS = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS, default='OPEN')
    assigned_to = models.ForeignKey(
        'team.TeamMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_requests',
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.title} — {self.property}"
