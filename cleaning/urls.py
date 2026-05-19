from rest_framework.routers import DefaultRouter
from .views import CleaningTaskViewSet

router = DefaultRouter()
router.register(r'cleaning', CleaningTaskViewSet, basename='cleaning')

urlpatterns = router.urls
