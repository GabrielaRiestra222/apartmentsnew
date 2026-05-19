from rest_framework import serializers
from .models import BookingPayment


class BookingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPayment
        fields = '__all__'
