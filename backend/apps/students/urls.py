from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GuardianViewSet, MedicalRecordViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"", StudentViewSet, basename="student")

# Nested routes
guardian_list = GuardianViewSet.as_view({"get": "list", "post": "create"})
guardian_detail = GuardianViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

medical_record_list = MedicalRecordViewSet.as_view({"get": "list", "post": "create"})
medical_record_detail = MedicalRecordViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update"}
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:student_pk>/guardians/",
        guardian_list,
        name="student-guardian-list",
    ),
    path(
        "<int:student_pk>/guardians/<int:pk>/",
        guardian_detail,
        name="student-guardian-detail",
    ),
    path(
        "<int:student_pk>/medical-record/",
        medical_record_list,
        name="student-medical-record-list",
    ),
    path(
        "<int:student_pk>/medical-record/<int:pk>/",
        medical_record_detail,
        name="student-medical-record-detail",
    ),
]
