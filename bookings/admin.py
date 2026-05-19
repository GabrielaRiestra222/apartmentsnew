from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        'apartment',
        'check_in',
        'check_out',
        'total_price',
        'display_total_paid',
        'display_remaining_balance',
        'status'
    )

    readonly_fields = (
        'display_total_paid',
        'display_remaining_balance',
    )

    def display_total_paid(self, obj):
        return obj.total_paid
    display_total_paid.short_description = "Total Paid"

    def display_remaining_balance(self, obj):
        return obj.remaining_balance
    display_remaining_balance.short_description = "Remaining Balance"
