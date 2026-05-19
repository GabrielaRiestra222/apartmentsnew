from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'accounting', TransactionViewSet, basename='transaction')

urlpatterns = router.urls
