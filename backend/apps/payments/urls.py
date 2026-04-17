from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MonthlyFeeViewSet, PaymentViewSet

router = DefaultRouter()
# Register monthly-fees BEFORE the root payment viewset to avoid path conflicts
router.register(r"monthly-fees", MonthlyFeeViewSet, basename="monthly-fee")
router.register(r"", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
