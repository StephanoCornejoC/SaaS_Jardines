import logging
import traceback
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Guardian, MedicalRecord, Student

logger = logging.getLogger(__name__)

EDAD_MINIMA = 1
EDAD_MAXIMA = 6


def _calcular_edad(fecha_nacimiento):
    today = date.today()
    return (
        today.year
        - fecha_nacimiento.year
        - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )


def _validar_edad(fecha_nacimiento):
    if fecha_nacimiento is None:
        return
    if fecha_nacimiento > date.today():
        raise serializers.ValidationError(
            "La fecha de nacimiento no puede ser futura."
        )
    edad = _calcular_edad(fecha_nacimiento)
    if edad < EDAD_MINIMA or edad > EDAD_MAXIMA:
        raise serializers.ValidationError(
            f"La edad del alumno debe estar entre {EDAD_MINIMA} y {EDAD_MAXIMA} años."
        )


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = "__all__"
        read_only_fields = ("id", "student")


class GuardianInlineSerializer(serializers.ModelSerializer):
    """Serializer used when guardians arrive nested inside a Student payload."""

    class Meta:
        model = Guardian
        fields = (
            "id",
            "dni",
            "nombres",
            "apellidos",
            "telefono",
            "email",
            "parentesco",
            "es_principal",
        )
        extra_kwargs = {
            "id": {"read_only": False, "required": False},
        }


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        exclude = ("student",)
        read_only_fields = ("id",)


class StudentForTeacherSerializer(serializers.ModelSerializer):
    """
    Serializer "lite" para que profesores vean alumnos sin datos sensibles.

    Solo lo necesario para tomar asistencia: nombre, foto, aula. NO incluye
    DNI, apoderados, ficha médica, fecha de ingreso ni nada que la profesora
    no necesite para su tarea.
    """

    classroom_nombre = serializers.CharField(
        source="classroom.nombre", read_only=True, default=None
    )

    class Meta:
        model = Student
        fields = (
            "id",
            "nombres",
            "apellidos",
            "foto",
            "classroom",
            "classroom_nombre",
            "estado",
        )


class StudentListSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)
    classroom_nombre = serializers.CharField(
        source="classroom.nombre", read_only=True, default=None
    )
    apoderado_principal = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            "id",
            "dni",
            "nombres",
            "apellidos",
            "edad",
            "classroom",
            "classroom_nombre",
            "estado",
            "apoderado_principal",
        )

    def get_apoderado_principal(self, obj):
        # Materializa el prefetch_related una sola vez en lugar de evaluarlo
        # 3 veces (.all() en filter, en if y en first()). Para 50 alumnos esto
        # reduce ~150 evaluaciones de queryset a 50.
        guardians = list(obj.apoderados.all())
        if not guardians:
            return None
        guardian = next((g for g in guardians if g.es_principal), guardians[0])
        return {
            "id": guardian.id,
            "nombres": guardian.nombres,
            "apellidos": guardian.apellidos,
            "telefono": guardian.telefono,
            "email": guardian.email,
            "parentesco": guardian.parentesco,
        }


class StudentDetailSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)
    apoderados = GuardianInlineSerializer(many=True, required=False)
    ficha_medica = MedicalRecordSerializer(read_only=True)
    classroom_nombre = serializers.CharField(
        source="classroom.nombre", read_only=True, default=None
    )

    # Optional matricula payload to register the student in one go.
    # allow_empty=True para que multipart PATCH (sin matricula) no falle.
    matricula = serializers.DictField(
        write_only=True, required=False, allow_empty=True
    )

    class Meta:
        model = Student
        fields = (
            "id",
            "dni",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "genero",
            "foto",
            "ficha_matricula",
            "classroom",
            "classroom_nombre",
            "estado",
            "fecha_ingreso",
            "edad",
            "apoderados",
            "ficha_medica",
            "matricula",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_fecha_nacimiento(self, value):
        _validar_edad(value)
        return value

    def validate_apoderados(self, value):
        if value is None:
            return value
        if len(value) < 1:
            raise serializers.ValidationError(
                "Debe registrar al menos un apoderado."
            )
        if len(value) > 2:
            raise serializers.ValidationError(
                "Solo puede registrar hasta dos apoderados."
            )
        dnis = [a.get("dni") for a in value if a.get("dni")]
        if len(dnis) != len(set(dnis)):
            raise serializers.ValidationError(
                "Los apoderados no pueden compartir el mismo DNI."
            )
        return value

    def validate_matricula(self, value):
        if not value:
            return value
        anio = value.get("anio_escolar")
        if anio is None:
            raise serializers.ValidationError(
                {"anio_escolar": "Es obligatorio para registrar la matrícula."}
            )
        try:
            value["anio_escolar"] = int(anio)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {"anio_escolar": "Año escolar inválido."}
            )
        for campo in ("costo_matricula", "monto_mensual"):
            if value.get(campo) in (None, ""):
                raise serializers.ValidationError(
                    {campo: "Es obligatorio para registrar la matrícula."}
                )
            try:
                value[campo] = Decimal(str(value[campo]))
            except Exception as exc:
                raise serializers.ValidationError({campo: str(exc)})
        return value

    def create(self, validated_data):
        apoderados_data = validated_data.pop("apoderados", [])
        matricula_data = validated_data.pop("matricula", None)

        if not apoderados_data:
            raise serializers.ValidationError(
                {"apoderados": "Debe registrar al menos un apoderado."}
            )

        try:
            with transaction.atomic():
                student = super().create(validated_data)

                principal_marcado = False
                for idx, apo in enumerate(apoderados_data):
                    apo.pop("id", None)
                    if idx == 0 and not principal_marcado:
                        apo["es_principal"] = True
                        principal_marcado = True
                    elif apo.get("es_principal") and principal_marcado:
                        apo["es_principal"] = False
                    Guardian.objects.create(student=student, **apo)

                if matricula_data:
                    self._crear_matricula(student, matricula_data)
        except IntegrityError as exc:
            logger.warning("IntegrityError al crear alumno: %s", exc)
            mensaje = str(exc).lower()
            if "dni" in mensaje:
                raise serializers.ValidationError(
                    {"dni": "Ya existe un registro con ese DNI."}
                )
            raise serializers.ValidationError(
                {"detail": "No se pudo guardar el alumno. Verifica los datos."}
            )
        except serializers.ValidationError:
            raise
        except Exception as exc:
            logger.error(
                "Error inesperado al crear alumno: %s\n%s",
                exc,
                traceback.format_exc(),
            )
            raise serializers.ValidationError(
                {"detail": f"Error al guardar: {exc}"}
            )

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        apoderados_data = validated_data.pop("apoderados", None)
        validated_data.pop("matricula", None)

        student = super().update(instance, validated_data)

        if apoderados_data is not None:
            self._sync_apoderados(student, apoderados_data)

        return student

    def _crear_matricula(self, student, matricula_data):
        from apps.cashflow.models import CashCategory, CashTransaction
        from apps.enrollments.models import Enrollment
        from apps.payments.models import MonthlyFee

        request = self.context.get("request")
        anio = matricula_data["anio_escolar"]
        costo = matricula_data["costo_matricula"]
        monto_mensual = matricula_data["monto_mensual"]

        enrollment, _ = Enrollment.objects.update_or_create(
            student=student,
            anio_escolar=anio,
            defaults={
                "classroom": student.classroom,
                "costo_matricula": costo,
                "created_by": request.user
                if request and request.user.is_authenticated
                else None,
            },
        )

        MonthlyFee.objects.update_or_create(
            student=student,
            anio_escolar=anio,
            defaults={"monto_mensual": monto_mensual},
        )

        if costo and costo > 0:
            categoria, _ = CashCategory.objects.get_or_create(
                nombre="Matrículas",
                tipo=CashCategory.Tipo.INGRESO,
                defaults={"es_sistema": True},
            )
            CashTransaction.objects.create(
                categoria=categoria,
                descripcion=f"Matrícula {student} - {anio}",
                monto=costo,
                tipo=CashTransaction.Tipo.INGRESO,
                fecha=date.today(),
                creado_por=request.user
                if request and request.user.is_authenticated
                else None,
            )

        return enrollment

    def _sync_apoderados(self, student, apoderados_data):
        if len(apoderados_data) > 2:
            raise serializers.ValidationError(
                {"apoderados": "Solo puede registrar hasta dos apoderados."}
            )
        existentes = {g.id: g for g in student.apoderados.all()}
        ids_recibidos = []
        principal_marcado = False
        for idx, apo in enumerate(apoderados_data):
            apo_id = apo.pop("id", None)
            if idx == 0 and not principal_marcado:
                apo["es_principal"] = True
                principal_marcado = True
            elif apo.get("es_principal") and principal_marcado:
                apo["es_principal"] = False
            if apo_id and apo_id in existentes:
                guardian = existentes[apo_id]
                for field, value in apo.items():
                    setattr(guardian, field, value)
                guardian.save()
                ids_recibidos.append(apo_id)
            else:
                nuevo = Guardian.objects.create(student=student, **apo)
                ids_recibidos.append(nuevo.id)

        for old_id, guardian in existentes.items():
            if old_id not in ids_recibidos:
                guardian.delete()
