from django.db import models


class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('CLEANER', 'Limpieza'),
        ('CHECKIN', 'Entradas/Salidas'),
        ('MAINTENANCE', 'Mantenimiento'),
        ('ADMIN', 'Administración'),
    ]

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    photo = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"
