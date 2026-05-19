from rest_framework.routers import DefaultRouter
from .views import BookingPaymentViewSet

router = DefaultRouter()
router.register(r'', BookingPaymentViewSet, basename='payment')

urlpatterns = router.urls
