from django.contrib import admin
from .models import Agency


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'email', 'commission_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_name', 'email')
