import uuid
from django.db import models


class ChatSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    property = models.ForeignKey(
        'properties.Property',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_sessions',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    messages = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.session_id}"
