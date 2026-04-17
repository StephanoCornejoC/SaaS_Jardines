from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommunicationViewSet

router = DefaultRouter()
router.register(r"", CommunicationViewSet, basename="communication")

urlpatterns = [
    path("", include(router.urls)),
]
