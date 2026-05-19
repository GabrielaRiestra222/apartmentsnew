from django.contrib import admin
from .models import CleaningTask


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ('property', 'scheduled_date', 'assigned_to', 'status', 'fee')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('property__title', 'assigned_to')
