import anthropic
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import ChatSession
from .serializers import ChatMessageInputSerializer
from faq.models import FAQ
from properties.models import Property


class ChatbotMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatMessageInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_message = data['message']
        property_id = data.get('property_id')
        session_id = data.get('session_id')

        # --- Load or create chat session ---
        if session_id:
            session, _ = ChatSession.objects.get_or_create(
                session_id=session_id,
                defaults={'property_id': property_id},
            )
        else:
            session = ChatSession.objects.create(property_id=property_id)

        # --- Build context: property info ---
        property_info = ''
        if property_id:
            try:
                prop = Property.objects.get(pk=property_id)
                property_info = (
                    f"Property: {prop.title}\n"
                    f"Location: {prop.location}\n"
                    f"Price per night: {prop.price_per_night}\n"
                    f"Max guests: {prop.max_guests}\n"
                    f"Description: {prop.description}\n"
                )
                if hasattr(prop, 'check_in_time'):
                    property_info += f"Check-in time: {prop.check_in_time}\n"
                    property_info += f"Check-out time: {prop.check_out_time}\n"
                if hasattr(prop, 'rules') and prop.rules:
                    property_info += f"House rules: {prop.rules}\n"
            except Property.DoesNotExist:
                pass

        # --- Build context: published FAQs ---
        faqs = FAQ.objects.filter(is_published=True).select_related('category').order_by('order')
        faq_list = '\n'.join(
            f"Q: {faq.question}\nA: {faq.answer}" for faq in faqs
        )

        system_prompt = (
            "You are a helpful assistant for a vacation rental company.\n"
            "Answer questions about properties, availability, check-in, rules and policies.\n"
            "Always answer in the same language the user writes in.\n"
            "Never invent prices or dates not provided below.\n"
            "If unsure, suggest contacting the host directly.\n\n"
            f"PROPERTIES INFO:\n{property_info or 'No specific property selected.'}\n\n"
            f"FREQUENTLY ASKED QUESTIONS:\n{faq_list or 'No FAQs available.'}"
        )

        # --- Call Anthropic API ---
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        ai_response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=500,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        reply = ai_response.content[0].text

        # --- Persist messages to session ---
        messages = list(session.messages)
        messages.append({'role': 'user', 'content': user_message})
        messages.append({'role': 'assistant', 'content': reply})
        session.messages = messages
        session.save(update_fields=['messages'])

        return Response({
            'reply': reply,  # Cambiado de 'response' a 'reply'
            'session_id': str(session.session_id),
        })


# Alias so both import names work
ChatbotView = ChatbotMessageView
