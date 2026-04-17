from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TeacherContractViewSet, TeacherPaymentViewSet, TeacherViewSet

router = DefaultRouter()
router.register(r"", TeacherViewSet, basename="teacher")

# Nested routes for contracts
contract_list = TeacherContractViewSet.as_view({"get": "list", "post": "create"})
contract_detail = TeacherContractViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

# Nested routes for payments
payment_list = TeacherPaymentViewSet.as_view({"get": "list", "post": "create"})
payment_detail = TeacherPaymentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:teacher_pk>/contracts/",
        contract_list,
        name="teacher-contract-list",
    ),
    path(
        "<int:teacher_pk>/contracts/<int:pk>/",
        contract_detail,
        name="teacher-contract-detail",
    ),
    path(
        "<int:teacher_pk>/contracts/<int:contract_pk>/payments/",
        payment_list,
        name="teacher-payment-list",
    ),
    path(
        "<int:teacher_pk>/contracts/<int:contract_pk>/payments/<int:pk>/",
        payment_detail,
        name="teacher-payment-detail",
    ),
]
