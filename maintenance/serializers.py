from rest_framework import serializers
from .models import MaintenanceRequest


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)
    assigned_to_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
        read_only_fields = ('reported_at',)

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return ''
        return f'{obj.assigned_to.first_name} {obj.assigned_to.last_name}'.strip()

    def to_internal_value(self, data):
        mutable_data = data.copy()

        if mutable_data.get('assigned_to') == '':
            mutable_data['assigned_to'] = None

        if mutable_data.get('cost') in ('', None):
            mutable_data['cost'] = 0

        return super().to_internal_value(mutable_data)
