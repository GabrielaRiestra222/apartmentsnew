from rest_framework import serializers
from .models import CalendarBlock


class CalendarBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarBlock
        fields = '__all__'

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': 'Debe ser igual o posterior a la fecha de inicio.'})
        return attrs
