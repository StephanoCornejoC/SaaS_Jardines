from datetime import date
from decimal import Decimal
from io import BytesIO

from django.db.models import Count, Q
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminJardinOrAbove
from shared.validators import validate_month_param, validate_year_param


def _style_header(ws, headers, row=1):
    """Aplica estilos al encabezado de una hoja."""
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border


def _build_response(wb, filename):
    """Genera HttpResponse con el archivo Excel."""
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet para generación de reportes Excel.
    """
    permission_classes = [IsAdminJardinOrAbove]

    @action(detail=False, methods=["get"], url_path="morosidad-excel")
    def morosidad_excel(self, request):
        """Genera reporte Excel de pagos vencidos (morosidad)."""
        from apps.payments.models import Payment

        mes = validate_month_param(request.query_params.get("mes"))
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year

        payments_qs = Payment.objects.filter(
            estado=Payment.Estado.VENCIDO,
        ).select_related("student", "student__classroom")

        if mes:
            payments_qs = payments_qs.filter(mes=mes)
        payments_qs = payments_qs.filter(anio=anio)

        wb = Workbook()
        ws = wb.active
        ws.title = "Morosidad"

        headers = [
            "Alumno",
            "DNI",
            "Aula",
            "Mes",
            "Año",
            "Monto",
            "Fecha Vencimiento",
            "Días Vencido",
        ]
        _style_header(ws, headers)

        today = date.today()
        for row_idx, payment in enumerate(payments_qs, 2):
            dias_vencido = (today - payment.fecha_vencimiento).days
            ws.cell(row=row_idx, column=1, value=str(payment.student))
            ws.cell(row=row_idx, column=2, value=payment.student.dni)
            ws.cell(
                row=row_idx,
                column=3,
                value=str(payment.student.classroom) if payment.student.classroom else "Sin aula",
            )
            ws.cell(row=row_idx, column=4, value=payment.mes)
            ws.cell(row=row_idx, column=5, value=payment.anio)
            ws.cell(row=row_idx, column=6, value=payment.monto)
            ws.cell(
                row=row_idx,
                column=7,
                value=payment.fecha_vencimiento.strftime("%d/%m/%Y"),
            )
            ws.cell(row=row_idx, column=8, value=dias_vencido)

        # Ajustar ancho de columnas
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[chr(64 + col)].width = 18

        filename = f"morosidad_{anio}.xlsx"
        return _build_response(wb, filename)

    @action(detail=False, methods=["get"], url_path="alumnos-excel")
    def alumnos_excel(self, request):
        """Genera reporte Excel con la lista de alumnos."""
        from apps.students.models import Student

        estado = request.query_params.get("estado", "ACTIVO")

        students_qs = Student.objects.select_related("classroom")
        if estado:
            students_qs = students_qs.filter(estado=estado)

        wb = Workbook()
        ws = wb.active
        ws.title = "Alumnos"

        headers = [
            "Apellidos",
            "Nombres",
            "DNI",
            "Fecha Nacimiento",
            "Edad",
            "Género",
            "Aula",
            "Estado",
            "Fecha Ingreso",
        ]
        _style_header(ws, headers)

        for row_idx, student in enumerate(students_qs, 2):
            ws.cell(row=row_idx, column=1, value=student.apellidos)
            ws.cell(row=row_idx, column=2, value=student.nombres)
            ws.cell(row=row_idx, column=3, value=student.dni)
            ws.cell(
                row=row_idx,
                column=4,
                value=student.fecha_nacimiento.strftime("%d/%m/%Y"),
            )
            ws.cell(row=row_idx, column=5, value=student.edad)
            ws.cell(row=row_idx, column=6, value=student.get_genero_display())
            ws.cell(
                row=row_idx,
                column=7,
                value=str(student.classroom) if student.classroom else "Sin aula",
            )
            ws.cell(row=row_idx, column=8, value=student.get_estado_display())
            ws.cell(
                row=row_idx,
                column=9,
                value=student.fecha_ingreso.strftime("%d/%m/%Y"),
            )

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[chr(64 + col)].width = 18

        filename = f"alumnos_{estado.lower()}.xlsx"
        return _build_response(wb, filename)

    @action(detail=False, methods=["get"], url_path="asistencia-excel")
    def asistencia_excel(self, request):
        """Genera reporte Excel de asistencia por aula y mes."""
        from apps.attendance.models import Attendance
        from apps.classrooms.models import Classroom

        classroom_id = request.query_params.get("classroom_id")
        mes = validate_month_param(request.query_params.get("mes")) or date.today().month
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year

        if not classroom_id:
            return Response(
                {"error": "Se requiere el parámetro classroom_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            classroom = Classroom.objects.get(pk=int(classroom_id))
        except Classroom.DoesNotExist:
            return Response(
                {"error": "Aula no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        attendances = Attendance.objects.filter(
            classroom=classroom,
            fecha__month=mes,
            fecha__year=anio,
        ).select_related("student")

        # Agrupar por alumno
        report = (
            attendances.values("student__apellidos", "student__nombres")
            .annotate(
                total_presentes=Count("id", filter=Q(estado=Attendance.Estado.PRESENTE)),
                total_ausentes=Count("id", filter=Q(estado=Attendance.Estado.AUSENTE)),
                total_tardanzas=Count("id", filter=Q(estado=Attendance.Estado.TARDANZA)),
                total_justificados=Count(
                    "id", filter=Q(estado=Attendance.Estado.JUSTIFICADO)
                ),
                total_dias=Count("id"),
            )
            .order_by("student__apellidos", "student__nombres")
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Asistencia"

        # Titulo
        ws.merge_cells("A1:H1")
        title_cell = ws.cell(
            row=1,
            column=1,
            value=f"Reporte de Asistencia - {classroom.nombre} - {mes}/{anio}",
        )
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")

        headers = [
            "Alumno",
            "Presentes",
            "Ausentes",
            "Tardanzas",
            "Justificados",
            "Total Días",
            "% Asistencia",
        ]
        _style_header(ws, headers, row=3)

        for row_idx, row in enumerate(report, 4):
            nombre = f"{row['student__apellidos']}, {row['student__nombres']}"
            total = row["total_dias"]
            porcentaje = (row["total_presentes"] / total * 100) if total > 0 else 0

            ws.cell(row=row_idx, column=1, value=nombre)
            ws.cell(row=row_idx, column=2, value=row["total_presentes"])
            ws.cell(row=row_idx, column=3, value=row["total_ausentes"])
            ws.cell(row=row_idx, column=4, value=row["total_tardanzas"])
            ws.cell(row=row_idx, column=5, value=row["total_justificados"])
            ws.cell(row=row_idx, column=6, value=total)
            ws.cell(row=row_idx, column=7, value=f"{porcentaje:.1f}%")

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[chr(64 + col)].width = 18

        filename = f"asistencia_{classroom.nombre}_{mes}_{anio}.xlsx"
        return _build_response(wb, filename)

    @action(detail=False, methods=["get"], url_path="cashflow-excel")
    def cashflow_excel(self, request):
        """Genera reporte Excel de ingresos y egresos."""
        from apps.cashflow.models import CashTransaction

        mes = validate_month_param(request.query_params.get("mes"))
        anio = validate_year_param(request.query_params.get("anio")) or date.today().year

        transactions_qs = CashTransaction.objects.filter(
            fecha__year=anio
        ).select_related("categoria")

        if mes:
            transactions_qs = transactions_qs.filter(fecha__month=mes)

        wb = Workbook()
        ws = wb.active
        ws.title = "Flujo de Caja"

        # Titulo
        periodo = f"{mes}/{anio}" if mes else str(anio)
        ws.merge_cells("A1:G1")
        title_cell = ws.cell(
            row=1, column=1, value=f"Reporte de Flujo de Caja - {periodo}"
        )
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")

        headers = [
            "Fecha",
            "Tipo",
            "Categoría",
            "Descripción",
            "Monto",
        ]
        _style_header(ws, headers, row=3)

        total_ingresos = Decimal("0")
        total_egresos = Decimal("0")

        for row_idx, tx in enumerate(transactions_qs.order_by("fecha"), 4):
            ws.cell(row=row_idx, column=1, value=tx.fecha.strftime("%d/%m/%Y"))
            ws.cell(row=row_idx, column=2, value=tx.get_tipo_display())
            ws.cell(row=row_idx, column=3, value=str(tx.categoria))
            ws.cell(row=row_idx, column=4, value=tx.descripcion)
            ws.cell(row=row_idx, column=5, value=tx.monto)

            if tx.tipo == CashTransaction.Tipo.INGRESO:
                total_ingresos += tx.monto
            else:
                total_egresos += tx.monto

        # Resumen al final
        last_row = transactions_qs.count() + 5
        summary_font = Font(bold=True, size=11)

        ws.cell(row=last_row, column=3, value="Total Ingresos:").font = summary_font
        ws.cell(row=last_row, column=5, value=total_ingresos).font = summary_font

        ws.cell(row=last_row + 1, column=3, value="Total Egresos:").font = summary_font
        ws.cell(row=last_row + 1, column=5, value=total_egresos).font = summary_font

        ws.cell(row=last_row + 2, column=3, value="Balance:").font = summary_font
        balance_cell = ws.cell(
            row=last_row + 2, column=5, value=total_ingresos - total_egresos
        )
        balance_cell.font = summary_font

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[chr(64 + col)].width = 20

        filename = f"flujo_caja_{periodo.replace('/', '_')}.xlsx"
        return _build_response(wb, filename)
