from django.urls import path
from .views import AdminChatbotMessageView, ChatbotMessageView

urlpatterns = [
    path('chatbot/message/', ChatbotMessageView.as_view(), name='chatbot-message'),
    path('chatbot/admin-message/', AdminChatbotMessageView.as_view(), name='chatbot-admin-message'),
]
