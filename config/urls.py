from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Core existing apps
from organizations.views import OrganizationViewSet
from users.views import UserViewSet
from properties.views import (
    PropertyViewSet, PublicPropertyViewSet,
    AmenityViewSet, PropertyImageViewSet,
)
from clients.views import ClientViewSet
from sources.views import BookingSourceViewSet
from payments.views import BookingPaymentViewSet
from bookings.views import BookingViewSet

# New apps
from agencies.views import AgencyViewSet
from team.views import TeamMemberViewSet
from cleaning.views import CleaningTaskViewSet
from maintenance.views import MaintenanceRequestViewSet
from property_calendar.views import CalendarBlockViewSet
from accounting.views import TransactionViewSet
from faq.views import FAQCategoryViewSet, FAQViewSet, PublicFAQViewSet
from integrations.views import (
    AutomationEventViewSet,
    AutomationWebhookViewSet,
    ChannelConnectionViewSet,
    DynamicPricingRuleViewSet,
    GuestCheckInViewSet,
    InboxMessageViewSet,
    PaymentIntentViewSet,
    SeasonalRateViewSet,
    SmartLockCodeViewSet,
)

# Stand-alone views
from common.views import DashboardStatsView
from chatbot.urls import urlpatterns as chatbot_urlpatterns

router = DefaultRouter()

# Core
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'users', UserViewSet, basename='user')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'property-images', PropertyImageViewSet, basename='property-image')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'sources', BookingSourceViewSet, basename='source')
router.register(r'payments', BookingPaymentViewSet, basename='payment')
router.register(r'bookings', BookingViewSet, basename='booking')

# New
router.register(r'agencies', AgencyViewSet, basename='agency')
router.register(r'team', TeamMemberViewSet, basename='team-member')
router.register(r'cleaning', CleaningTaskViewSet, basename='cleaning')
router.register(r'maintenance', MaintenanceRequestViewSet, basename='maintenance')
router.register(r'calendar', CalendarBlockViewSet, basename='calendar')
router.register(r'accounting', TransactionViewSet, basename='transaction')
router.register(r'faq/categories', FAQCategoryViewSet, basename='faq-category')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'channel-connections', ChannelConnectionViewSet, basename='channel-connection')
router.register(r'seasonal-rates', SeasonalRateViewSet, basename='seasonal-rate')
router.register(r'inbox-messages', InboxMessageViewSet, basename='inbox-message')
router.register(r'guest-checkins', GuestCheckInViewSet, basename='guest-checkin')
router.register(r'smart-lock-codes', SmartLockCodeViewSet, basename='smart-lock-code')
router.register(r'dynamic-pricing-rules', DynamicPricingRuleViewSet, basename='dynamic-pricing-rule')
router.register(r'payment-intents', PaymentIntentViewSet, basename='payment-intent')
router.register(r'automation-webhooks', AutomationWebhookViewSet, basename='automation-webhook')
router.register(r'automation-events', AutomationEventViewSet, basename='automation-event')

# Public (no auth)
router.register(r'public/properties', PublicPropertyViewSet, basename='public-property')
router.register(r'public/faq', PublicFAQViewSet, basename='public-faq')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(chatbot_urlpatterns)),
    path('api/', include('integrations.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
