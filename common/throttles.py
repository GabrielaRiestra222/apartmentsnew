from rest_framework.throttling import AnonRateThrottle


class ContactRateThrottle(AnonRateThrottle):
    rate = '10/hour'


class PublicBookingRateThrottle(AnonRateThrottle):
    rate = '10/hour'


class PublicChatRateThrottle(AnonRateThrottle):
    # Cada mensaje cuesta una llamada a la API de Anthropic.
    rate = '30/hour'
