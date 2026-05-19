from rest_framework import serializers
from .models import ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'
        read_only_fields = ('started_at',)


class ChatMessageInputSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(max_length=2000)
    property_id = serializers.IntegerField(required=False, allow_null=True)
