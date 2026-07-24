from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConsentDocumentViewSet, ConsentViewSet

router = DefaultRouter()
router.register(r"documentos", ConsentDocumentViewSet, basename="consent-document")
router.register(r"registros", ConsentViewSet, basename="consent")

urlpatterns = [
    path("", include(router.urls)),
]
