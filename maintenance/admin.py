from django.contrib import admin
from .models import MaintenanceRequest


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'priority', 'status', 'assigned_to', 'reported_at')
    list_filter = ('priority', 'status')
    search_fields = ('title', 'property__title', 'assigned_to')
