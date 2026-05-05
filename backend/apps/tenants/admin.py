import re
import secrets
from datetime import date, timedelta
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django_tenants.utils import schema_context

from apps.platform.models import Plan, TenantSubscription
from apps.users.models import User

from .models import Domain, Tenant


BASE_DOMAIN = getattr(settings, "TENANT_BASE_DOMAIN", "corem.pe")
PRECIO_DEFAULT = Decimal("120.00")
TRIAL_DEFAULT = 30


def _slug(value):
    s = re.sub(r"[^a-z0-9]+", "", value.lower())
    return s[:30] or "jardin"


def _contar_alumnos(schema_name):
    """Cuenta alumnos activos del tenant de forma segura."""
    try:
        with schema_context(schema_name):
            from apps.students.models import Student
            return Student.objects.filter(estado="ACTIVO").count()
    except Exception:
        return "—"


# ============================================================================
# Formulario: Crear nuevo jardín
# ============================================================================

class CrearJardinForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre del jardín",
        max_length=255,
        help_text="Ej: Jardín Garabato",
    )
    ruc = forms.CharField(label="RUC", max_length=11)
    email_director = forms.EmailField(
        label="Correo del director(a)",
        help_text="Recibirá la contraseña inicial",
    )
    nombres_director = forms.CharField(label="Nombres", max_length=80)
    apellidos_director = forms.CharField(label="Apellidos", max_length=80)
    telefono = forms.CharField(label="Teléfono", required=False, max_length=20)
    direccion = forms.CharField(
        label="Dirección", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )
    precio_mensual = forms.DecimalField(
        label="Precio mensual (S/.)",
        max_digits=10,
        decimal_places=2,
        initial=PRECIO_DEFAULT,
        min_value=Decimal("50.00"),
        max_value=Decimal("500.00"),
        help_text="Precio personalizado para este jardín. Default: S/. 120.00",
    )
    dias_trial = forms.IntegerField(
        label="Días de trial",
        initial=TRIAL_DEFAULT,
        min_value=0,
        max_value=180,
        help_text="Días sin cobro desde el alta. Default: 30. Pon 0 para cobrar desde el inicio.",
    )
    dia_cobro = forms.IntegerField(
        label="Día de cobro mensual",
        initial=1,
        min_value=1,
        max_value=28,
        help_text="Día del mes en que se emitirá el cobro recurrente (1-28). Default: 01.",
    )
    schema_name = forms.SlugField(
        label="Schema (técnico)",
        help_text="Identificador único en BD. Solo letras/números. Default = nombre normalizado.",
        required=False,
    )
    dominio = forms.CharField(
        label="Dominio",
        help_text=f"Default: <nombre>.{BASE_DOMAIN}. Edita si el jardín tiene dominio propio.",
        required=False,
    )

    def clean(self):
        data = super().clean()
        nombre = (data.get("nombre") or "").strip()
        if not data.get("schema_name") and nombre:
            data["schema_name"] = _slug(nombre)
        if not data.get("dominio") and data.get("schema_name"):
            data["dominio"] = f"{data['schema_name']}.{BASE_DOMAIN}"
        if data.get("schema_name") and Tenant.objects.filter(schema_name=data["schema_name"]).exists():
            self.add_error("schema_name", "Ya existe un jardín con ese schema.")
        if data.get("dominio") and Domain.objects.filter(domain=data["dominio"]).exists():
            self.add_error("dominio", "Ese dominio ya está registrado.")
        if data.get("ruc") and Tenant.objects.filter(ruc=data["ruc"]).exists():
            self.add_error("ruc", "Ya existe un jardín con ese RUC.")
        return data


# ============================================================================
# TenantAdmin
# ============================================================================

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = (
        "nombre",
        "schema_name",
        "ruc",
        "alumnos_activos",
        "estado_subscription",
        "dias_info",
        "activo",
        "operar_link",
    )
    list_filter = ("activo",)
    search_fields = ("nombre", "ruc", "schema_name", "email")
    readonly_fields = ("schema_name", "created_at", "updated_at")
    ordering = ("nombre",)
    change_list_template = "admin/tenants/tenant/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "crear-jardin/",
                self.admin_site.admin_view(self.crear_jardin_view),
                name="tenants_tenant_crear_jardin",
            ),
        ]
        return custom + urls

    # ------------------------------------------------------------------
    # Columnas calculadas
    # ------------------------------------------------------------------

    @admin.display(description="Alumnos")
    def alumnos_activos(self, obj):
        if obj.schema_name in ("public", "info"):
            return "—"
        n = _contar_alumnos(obj.schema_name)
        return format_html(
            '<span style="font-weight:700;color:#0d9488">{}</span>', n
        )

    @admin.display(description="Estado")
    def estado_subscription(self, obj):
        sub = getattr(obj, "suscripcion", None)
        if not sub:
            return format_html(
                '<span style="color:#94a3b8;font-size:11px">Sin suscripción</span>'
            )
        colors = {
            "TRIAL":     "#3b82f6",
            "ACTIVA":    "#10b981",
            "MOROSA":    "#f59e0b",
            "BLOQUEADA": "#ef4444",
            "CANCELADA": "#6b7280",
        }
        c = colors.get(sub.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;border-radius:4px;'
            'font-size:11px;font-weight:600">{}</span>',
            c, sub.get_estado_display(),
        )

    @admin.display(description="Vencimiento")
    def dias_info(self, obj):
        sub = getattr(obj, "suscripcion", None)
        if not sub:
            return "—"
        hoy = date.today()
        if sub.estado == "TRIAL" and sub.trial_hasta:
            delta = (sub.trial_hasta - hoy).days
            if delta < 0:
                return format_html('<span style="color:#ef4444;font-weight:600">Trial vencido</span>')
            return format_html(
                '<span style="color:#3b82f6">Trial: {} días</span>', delta
            )
        from apps.platform.models import PlatformInvoice
        ultima = (
            PlatformInvoice.objects.filter(
                tenant=obj, estado=PlatformInvoice.Estado.PENDIENTE
            )
            .order_by("-fecha_vencimiento")
            .first()
        )
        if not ultima:
            return format_html('<span style="color:#10b981">Al día ✓</span>')
        delta = (hoy - ultima.fecha_vencimiento).days
        if delta > 0:
            color = "#ef4444" if delta >= 7 else "#f59e0b"
            return format_html(
                '<span style="color:{};font-weight:600">{} días vencida</span>', color, delta
            )
        return format_html(
            '<span style="color:#64748b">Vence en {} días</span>', abs(delta)
        )

    @admin.display(description="Panel")
    def operar_link(self, obj):
        if obj.schema_name in ("public", "info"):
            return "—"
        url = reverse("admin:jardin_dashboard", args=[obj.schema_name])
        return format_html(
            '<a href="{}" class="corem-operar-btn">Entrar →</a>', url
        )

    # ------------------------------------------------------------------
    # Vista: Crear nuevo jardín
    # ------------------------------------------------------------------

    def crear_jardin_view(self, request):
        if request.method == "POST":
            form = CrearJardinForm(request.POST)
            if form.is_valid():
                try:
                    tenant = self._crear_jardin(form.cleaned_data, request.user)
                except Exception as e:
                    messages.error(request, f"Error al crear el jardín: {e}")
                else:
                    messages.success(
                        request,
                        f"Jardín '{tenant.nombre}' creado. "
                        f"Credenciales enviadas a {form.cleaned_data['email_director']}.",
                    )
                    return redirect("admin:tenants_tenant_changelist")
        else:
            form = CrearJardinForm()
        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Crear nuevo jardín",
            "opts": self.model._meta,
            "base_domain": BASE_DOMAIN,
        }
        return render(request, "admin/tenants/tenant/crear_jardin.html", context)

    @transaction.atomic
    def _crear_jardin(self, data, creador):
        tenant = Tenant.objects.create(
            schema_name=data["schema_name"],
            nombre=data["nombre"],
            ruc=data["ruc"],
            email=data["email_director"],
            telefono=data.get("telefono") or "",
            direccion=data.get("direccion") or "",
            activo=True,
        )
        Domain.objects.create(domain=data["dominio"], tenant=tenant, is_primary=True)

        plan = Plan.vigente()
        if not plan:
            plan = Plan.objects.create(nombre="Plan COREM", precio_mensual=PRECIO_DEFAULT, activo=True)

        precio = data.get("precio_mensual") or plan.precio_mensual
        dias = int(data.get("dias_trial") or 0)
        hoy = date.today()
        trial_hasta = hoy + timedelta(days=dias) if dias > 0 else hoy
        estado_inicial = (
            TenantSubscription.Estado.TRIAL if dias > 0 else TenantSubscription.Estado.ACTIVA
        )

        TenantSubscription.objects.create(
            tenant=tenant,
            plan=plan,
            precio_acordado=precio,
            fecha_alta=hoy,
            trial_hasta=trial_hasta,
            dia_cobro=int(data.get("dia_cobro") or 1),
            estado=estado_inicial,
        )

        password = secrets.token_urlsafe(10)
        with schema_context(tenant.schema_name):
            user = User.objects.create_user(
                email=data["email_director"],
                first_name=data["nombres_director"],
                last_name=data["apellidos_director"],
                password=password,
            )
            user.is_staff = True
            user.is_superuser = True
            user.role = "ADMIN_JARDIN"
            user.save()

        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f"Bienvenido a COREM — Acceso a {tenant.nombre}",
                message=(
                    f"Hola {data['nombres_director']},\n\n"
                    f"Su jardín '{tenant.nombre}' ya está activo en COREM.\n\n"
                    f"URL: http://{data['dominio']}\n"
                    f"Usuario: {data['email_director']}\n"
                    f"Contraseña inicial: {password}\n\n"
                    f"Le recomendamos cambiar la contraseña al ingresar.\n\n"
                    f"— Equipo COREM"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[data["email_director"]],
                fail_silently=True,
            )
        except Exception:
            pass

        return tenant


# ============================================================================
# DomainAdmin
# ============================================================================

@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain", "tenant__nombre")
    autocomplete_fields = ("tenant",)
