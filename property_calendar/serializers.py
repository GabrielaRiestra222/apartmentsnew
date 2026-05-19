from rest_framework import serializers
from .models import CalendarBlock


class CalendarBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarBlock
        fields = '__all__'
