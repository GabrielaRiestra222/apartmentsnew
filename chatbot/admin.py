from django.contrib import admin
from .models import ChatSession


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'property', 'started_at')
    search_fields = ('session_id',)
    readonly_fields = ('session_id', 'started_at', 'messages')
