from rest_framework import serializers
from .models import CleaningTask


class CleaningTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CleaningTask
        fields = '__all__'
        read_only_fields = ('created_at',)
