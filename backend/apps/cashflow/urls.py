from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CashCategoryViewSet, CashTransactionViewSet, MonthlyClosureViewSet

router = DefaultRouter()
router.register(r"cash-categories", CashCategoryViewSet, basename="cash-category")
router.register(r"cash-transactions", CashTransactionViewSet, basename="cash-transaction")
router.register(r"monthly-closures", MonthlyClosureViewSet, basename="monthly-closure")

urlpatterns = [
    path("", include(router.urls)),
]
