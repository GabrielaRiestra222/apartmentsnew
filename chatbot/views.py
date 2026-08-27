from datetime import date, timedelta

import anthropic
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .models import ChatSession
from .serializers import AdminChatMessageInputSerializer, ChatMessageInputSerializer
from faq.models import FAQ
from integrations.models import InboxMessage
from properties.models import Property
from bookings.models import Booking


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

        InboxMessage.objects.create(
            channel='DIRECT',
            direction='INBOUND',
            sender=str(session.session_id),
            recipient='web',
            body=user_message,
            external_id=f'chat-{session.session_id}-{len(session.messages)}-in',
        )

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
            "You are a helpful, friendly assistant for a vacation rental company, chatting with a "
            "prospective or current guest through a plain-text chat widget.\n"
            "Answer questions about properties, availability, check-in, rules and policies.\n"
            "Always answer in the same language the user writes in.\n"
            "Never invent prices or dates not provided below.\n"
            "If unsure, suggest contacting the host directly — but only as a last resort, not the default answer.\n\n"
            "FORMATTING: reply in plain conversational text only. Never use markdown — no headings (#), "
            "no bold (**), no bullet points or numbered lists, no emoji as list markers. Write like a "
            "normal chat message: short paragraphs, 2-4 sentences unless the user clearly wants more detail. "
            "If you list a few options, do it inline in a sentence, not as a list.\n\n"
            "If no specific property is selected, still answer general questions (e.g. 'do you allow pets?') "
            "as best you can using the info below across all properties, instead of asking the guest to pick "
            "one first — only ask for a property if the answer genuinely differs per property and you need "
            "to know which one.\n\n"
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

        InboxMessage.objects.create(
            channel='DIRECT',
            direction='OUTBOUND',
            sender='assistant',
            recipient=str(session.session_id),
            body=reply,
            external_id=f'chat-{session.session_id}-{len(session.messages)}-out',
            is_read=True,
        )

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


class AdminChatbotMessageView(APIView):
    """Internal assistant for CRM staff — has access to real bookings/properties."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AdminChatMessageInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_message = data['message']
        history = data.get('history', [])

        org = request.user.organization
        properties_qs = Property.objects.all() if org is None else Property.objects.filter(organization=org)
        properties = properties_qs.order_by('title')

        today = date.today()
        upcoming_cutoff = today + timedelta(days=90)
        bookings_qs = Booking.objects.all() if org is None else Booking.objects.filter(apartment__organization=org)
        bookings = (
            bookings_qs
            .filter(check_out__gte=today - timedelta(days=30), check_in__lte=upcoming_cutoff)
            .select_related('apartment', 'client')
            .order_by('check_in')[:50]
        )

        properties_info = '\n'.join(
            f"- [{p.id}] {p.title} | {p.location} | {p.price_per_night}€/noche | "
            f"{'publicada' if p.is_published else 'borrador'} | {'activa' if p.is_active else 'inactiva'}"
            for p in properties
        ) or 'No hay propiedades registradas.'

        bookings_info = '\n'.join(
            f"- Reserva #{b.id} | {b.apartment.title} | "
            f"{b.client_name or (b.client.first_name + ' ' + b.client.last_name if b.client else 'sin cliente')} | "
            f"{b.check_in} → {b.check_out} | estado: {b.status} | "
            f"total: {b.total_price}€ | pagado: {b.total_paid}€ | pendiente: {b.remaining_balance}€"
            for b in bookings
        ) or 'No hay reservas en los últimos 30 días ni próximos 90 días.'

        system_prompt = (
            "You are the internal assistant for the staff of a vacation rental management company, "
            "used inside their private admin CRM. You are talking to a staff member, not a guest — "
            "you DO have access to their real booking and property data below, so use it directly "
            "instead of telling them to contact support or log into an admin panel (they already are).\n"
            "Always answer in the same language the user writes in. Be concise and concrete. "
            "Never invent bookings, prices or availability not listed below.\n"
            "Reply in plain conversational text, no markdown headings or bold — a short inline list "
            "separated by commas or line breaks is fine, but avoid heavy formatting.\n\n"
            f"ORGANIZATION: {org.name if org else 'all organizations (staff has no org assigned)'}\n\n"
            f"PROPERTIES:\n{properties_info}\n\n"
            f"BOOKINGS (last 30 days + next 90 days):\n{bookings_info}"
        )

        messages = [{'role': turn['role'], 'content': turn['content']} for turn in history]
        messages.append({'role': 'user', 'content': user_message})

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        ai_response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=700,
            system=system_prompt,
            messages=messages,
        )
        reply = ai_response.content[0].text

        return Response({'reply': reply})


# Alias so both import names work
ChatbotView = ChatbotMessageView
