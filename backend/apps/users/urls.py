from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .single_session import (
    SingleSessionRefreshMixin,
    SingleSessionTokenObtainPairSerializer,
)
from .views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")


class SingleSessionLoginView(TokenObtainPairView):
    """Login que enforza sesión única (regenera active_session_id en User)."""

    serializer_class = SingleSessionTokenObtainPairSerializer


class SingleSessionRefreshSerializer(SingleSessionRefreshMixin, TokenRefreshSerializer):
    """Preserva el sid original en el refresh del access token."""


class SingleSessionRefreshView(TokenRefreshView):
    serializer_class = SingleSessionRefreshSerializer


urlpatterns = [
    # JWT Auth con sesión única
    path("token/", SingleSessionLoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", SingleSessionRefreshView.as_view(), name="token_refresh"),
    # User CRUD + change-password
    path("", include(router.urls)),
]
