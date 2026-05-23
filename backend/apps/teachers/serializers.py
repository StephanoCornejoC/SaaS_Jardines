from rest_framework import serializers

from .models import Teacher, TeacherContract, TeacherPayment


class TeacherPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherPayment
        fields = "__all__"
        read_only_fields = ("id", "contract", "created_at")


class TeacherContractSerializer(serializers.ModelSerializer):
    payments = TeacherPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = TeacherContract
        fields = "__all__"
        read_only_fields = ("id", "teacher", "created_at")


def _active_contract(teacher):
    """Devuelve el contrato activo más reciente (o None).

    Aprovecha el `prefetch_related("contracts__payments")` del viewset
    iterando in-memory sobre `teacher.contracts.all()` para no disparar
    queries extras en el listado.
    """
    activos = [c for c in teacher.contracts.all() if c.activo]
    if not activos:
        return None
    activos.sort(key=lambda c: c.fecha_inicio, reverse=True)
    return activos[0]


class TeacherListSerializer(serializers.ModelSerializer):
    """Serializer del listado de profesores.

    Expone el sueldo del contrato activo (read-only) para que la directora
    lo vea en la tabla del frontend. La edición del sueldo se hace por el
    endpoint dedicado `actualizar-sueldo` (ver TeacherViewSet) — NO se
    edita acá para no exponer la complejidad del modelo TeacherContract.
    """
    nombre_completo = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    sueldo_actual = serializers.SerializerMethodField()
    contrato_id = serializers.SerializerMethodField()
    tipo_contrato = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            "id",
            "dni",
            "nombre_completo",
            "nombres",
            "apellidos",
            "tipo",
            "tipo_display",
            "especialidad",
            "telefono",
            "email",
            "fecha_ingreso",
            "sueldo_actual",
            "contrato_id",
            "tipo_contrato",
        )

    def get_nombre_completo(self, obj):
        return f"{obj.apellidos}, {obj.nombres}"

    def get_sueldo_actual(self, obj):
        c = _active_contract(obj)
        return str(c.sueldo) if c else None

    def get_contrato_id(self, obj):
        c = _active_contract(obj)
        return c.id if c else None

    def get_tipo_contrato(self, obj):
        c = _active_contract(obj)
        return c.tipo if c else None


class TeacherDetailSerializer(serializers.ModelSerializer):
    contracts = TeacherContractSerializer(many=True, read_only=True)
    sueldo_actual = serializers.SerializerMethodField()
    contrato_id = serializers.SerializerMethodField()
    tipo_contrato = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def get_sueldo_actual(self, obj):
        c = _active_contract(obj)
        return str(c.sueldo) if c else None

    def get_contrato_id(self, obj):
        c = _active_contract(obj)
        return c.id if c else None

    def get_tipo_contrato(self, obj):
        c = _active_contract(obj)
        return c.tipo if c else None
