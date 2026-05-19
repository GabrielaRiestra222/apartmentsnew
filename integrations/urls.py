from django.urls import path

from .views import n8n_inbound, property_ical_export, public_booking

urlpatterns = [
    path('public-booking/', public_booking, name='public-booking'),
    path('properties/<int:pk>/ical/', property_ical_export, name='property-ical-export'),
    path('integrations/n8n/inbound/', n8n_inbound, name='n8n-inbound'),
]
