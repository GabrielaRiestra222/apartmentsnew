from rest_framework.routers import DefaultRouter
from .views import BookingSourceViewSet

router = DefaultRouter()
router.register(r'', BookingSourceViewSet, basename='source')

urlpatterns = router.urls
