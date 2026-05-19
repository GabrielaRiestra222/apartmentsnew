from rest_framework import serializers
from .models import BookingSource


class BookingSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSource
        fields = '__all__'
