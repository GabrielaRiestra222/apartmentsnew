from rest_framework.routers import DefaultRouter
from .views import FAQCategoryViewSet, FAQViewSet, PublicFAQViewSet

router = DefaultRouter()
router.register(r'faq/categories', FAQCategoryViewSet, basename='faq-category')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'public/faq', PublicFAQViewSet, basename='public-faq')

urlpatterns = router.urls
