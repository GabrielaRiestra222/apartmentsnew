from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('category', 'subcategory', 'amount', 'date', 'property', 'booking')
    list_filter = ('category', 'date')
    search_fields = ('subcategory', 'description', 'property__title')
