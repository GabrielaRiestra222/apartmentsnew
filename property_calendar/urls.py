from rest_framework.routers import DefaultRouter
from .views import CalendarBlockViewSet

router = DefaultRouter()
router.register(r'calendar', CalendarBlockViewSet, basename='calendar')

urlpatterns = router.urls
