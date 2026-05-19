from django.urls import path
from .views import upload_property_image

urlpatterns = [
    path('upload-image/', upload_property_image, name='upload-property-image'),
]
