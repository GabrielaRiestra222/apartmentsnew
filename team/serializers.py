from rest_framework import serializers
from .models import TeamMember


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone',
            'role', 'is_active', 'photo', 'notes', 'created_at',
        )
        read_only_fields = ('created_at',)
