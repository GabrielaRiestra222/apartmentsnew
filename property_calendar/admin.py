from django.contrib import admin
from .models import CalendarBlock


@admin.register(CalendarBlock)
class CalendarBlockAdmin(admin.ModelAdmin):
    list_display = ('property', 'reason', 'start_date', 'end_date', 'booking')
    list_filter = ('reason',)
    search_fields = ('property__title',)
