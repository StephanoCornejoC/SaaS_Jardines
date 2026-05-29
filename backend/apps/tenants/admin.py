import logging
import re
import secrets
from datetime import date, timedelta

from django import forms
from django.conf import settings
from django.contrib import admin, messages

logger = logging.getLogger(__name__)
from django.contrib.admin import ModelAdmin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django_tenants.utils import schema_context

from apps.platform.models import Plan, TenantSubscription
from apps.platform.services import emitir_cobro_ahora
from apps.users.models import User

from .models import Domain, Tenant


# Subdominio base por defecto (configurable por env)
BASE_DOMAIN = getattr(settings, "TENANT_BASE_DOMAIN", "corem.pe")


def _slug(value):
    """Genera un schema_name seguro a partir del nombre del jardín."""
    s = re.sub(r"[^a-z0-9]+", "", value.lower())
    return s[:30] or "jardin"


class CrearJardinForm(forms.Form):
    """Formulario de alta de jardín nuevo desde el admin."""

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
    schema_name = forms.SlugField(
        label="Schema (técnico)",
        help_text="Identificador único en BD. Solo letras/números. Default = nombre normalizado.",
        required=False,
    )
    dominio = forms.CharField(
        label="Dominio",
        help_text=f"Default: <nombre>.{BASE_DOMAIN}. Puedes editarlo si el jardín tiene su propio dominio.",
        required=False,
    )

    def clean(self):
        data = super().clean()
        nombre = (data.get("nombre") or "").strip()
        if not data.get("schema_name") and nombre:
            data["schema_name"] = _slug(nombre)
        if not data.get("dominio") and data.get("schema_name"):
            data["dominio"] = f"{data['schema_name']}.{BASE_DOMAIN}"
        # Validaciones de unicidad
        if data.get("schema_name") and Tenant.objects.filter(schema_name=data["schema_name"]).exists():
            self.add_error("schema_name", "Ya existe un jardín con ese schema.")
        if data.get("dominio") and Domain.objects.filter(domain=data["dominio"]).exists():
            self.add_error("dominio", "Ese dominio ya está registrado.")
        if data.get("ruc") and Tenant.objects.filter(ruc=data["ruc"]).exists():
            self.add_error("ruc", "Ya existe un jardín con ese RUC.")
        return data


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = (
        "nombre",
        "schema_name",
        "ruc",
        "estado_subscription",
        "operar_link",
        "cobro_ahora_link",
        "activo",
        "created_at",
    )
    list_filter = ()
    search_fields = ("nombre", "ruc", "schema_name", "email")
    readonly_fields = ("schema_name", "created_at", "updated_at")
    ordering = ("nombre",)
    change_list_template = "admin/tenants/tenant/change_list.html"

    def get_queryset(self, request):
        # Excluimos los schemas técnicos (public/info) del changelist —
        # no son jardines clientes, no se pueden operar, y aparecer
        # confunde al SuperAdmin.
        qs = super().get_queryset(request)
        return qs.exclude(schema_name__in=("public", "info"))

    def has_add_permission(self, request):
        # Deshabilita el "Add" default del admin: el alta de un Tenant
        # requiere validaciones especiales (schema_name, dominio, director,
        # suscripción) que solo se hacen vía CrearJardinForm. El botón
        # custom "+ Crear nuevo jardín" del change_list ya lleva ahí.
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "crear-jardin/",
                self.admin_site.admin_view(self.crear_jardin_view),
                name="tenants_tenant_crear_jardin",
            ),
            path(
                "<int:tenant_id>/emitir-cobro/",
                self.admin_site.admin_view(self.emitir_cobro_view),
                name="tenants_tenant_emitir_cobro",
            ),
        ]
        return custom + urls

    @admin.display(description="Suscripción")
    def estado_subscription(self, obj):
        sub = getattr(obj, "suscripcion", None)
        if not sub:
            return format_html('<span style="color:#94a3b8">Sin suscripción</span>')
        colors = {
            "TRIAL": "#3b82f6",
            "ACTIVA": "#10b981",
            "MOROSA": "#f59e0b",
            "BLOQUEADA": "#ef4444",
            "CANCELADA": "#6b7280",
        }
        c = colors.get(sub.estado, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            c, sub.get_estado_display(),
        )

    @admin.display(description="Cobro")
    def cobro_ahora_link(self, obj):
        sub = getattr(obj, "suscripcion", None)
        if not sub or sub.estado in (
            TenantSubscription.Estado.CANCELADA,
            TenantSubscription.Estado.TRIAL,
        ):
            return "—"
        url = reverse("admin:tenants_tenant_emitir_cobro", args=[obj.id])
        return format_html(
            '<a href="{}" class="button" style="padding:4px 10px;background:#f59e0b;color:white;border-radius:4px;text-decoration:none;font-size:11px">Emitir cobro</a>',
            url,
        )

    def emitir_cobro_view(self, request, tenant_id):
        if request.method != "POST":
            tenant = Tenant.objects.filter(id=tenant_id).first()
            if not tenant:
                messages.error(request, "Jardín no encontrado.")
                return redirect("admin:tenants_tenant_changelist")
            return render(
                request,
                "admin/tenants/tenant/emitir_cobro_confirm.html",
                {
                    **self.admin_site.each_context(request),
                    "tenant": tenant,
                    "opts": self.model._meta,
                    "title": f"Emitir cobro — {tenant.nombre}",
                },
            )
        tenant = Tenant.objects.filter(id=tenant_id).first()
        if not tenant:
            messages.error(request, "Jardín no encontrado.")
            return redirect("admin:tenants_tenant_changelist")
        invoice, was_created, msg = emitir_cobro_ahora(tenant)
        if invoice:
            (messages.success if was_created else messages.info)(request, f"{tenant.nombre}: {msg}")
        else:
            messages.warning(request, f"{tenant.nombre}: {msg}")
        return redirect("admin:tenants_tenant_changelist")

    @admin.display(description="Operar")
    def operar_link(self, obj):
        # Apunta al modo Operar Jardín del CoremAdminSite: /admin/op/<schema>/.
        # Esa URL setea la sesión + redirige a /admin/ con el sidebar y
        # modelos del jardín seleccionado (Gestión escolar / Finanzas / etc).
        # No usar /admin/jardin/<schema>/ — ese URL pattern viejo se eliminó.
        url = f"/admin/op/{obj.schema_name}/"
        return format_html(
            '<a href="{}" class="button" style="padding:4px 10px;background:#0d9488;color:white;border-radius:4px;text-decoration:none;font-size:11px">Operar ↗</a>',
            url,
        )

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
                        f"Jardín '{tenant.nombre}' creado. La contraseña inicial se envió a {form.cleaned_data['email_director']}.",
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
        # 1. Crear tenant + schema
        tenant = Tenant.objects.create(
            schema_name=data["schema_name"],
            nombre=data["nombre"],
            ruc=data["ruc"],
            email=data["email_director"],
            telefono=data.get("telefono") or "",
            direccion=data.get("direccion") or "",
            activo=True,
        )
        # 2. Crear dominio
        Domain.objects.create(
            domain=data["dominio"], tenant=tenant, is_primary=True
        )
        # 3. Crear suscripción con trial 1 mes.
        # Un jardín nuevo arranca sin alumnos cargados → tier Mini por default.
        # Cuando la directora carga alumnos durante el trial, el tier real se
        # recalcula al cerrar el trial; soporte interno puede actualizarlo
        # manualmente desde el admin si conviene cobrar otro tier desde el
        # día 1.
        plan = Plan.por_alumnos(0)
        if not plan:
            # Edge case: ningún Plan activo. Avisa para que se corrija la
            # configuración antes de que el admin crashee.
            raise RuntimeError(
                "No hay planes activos en la base. "
                "Corre la migración platform/0003_plan_tiers o crea los planes "
                "manualmente antes de dar de alta un jardín."
            )
        TenantSubscription.objects.create(
            tenant=tenant,
            plan=plan,
            precio_acordado=plan.precio_mensual,
            fecha_alta=date.today(),
            trial_hasta=date.today() + timedelta(days=30),
            estado=TenantSubscription.Estado.TRIAL,
        )
        # 4. Crear usuario admin del jardín + categorías sistema en su schema
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

            # Pre-crear las 4 categorías sistema (Pensiones/Otros INGRESO +
            # Sueldos/Otros EGRESO) para que aparezcan en el selector de
            # Caja desde el día 1, sin esperar al primer pago real.
            from apps.cashflow.services import ensure_categorias_sistema
            ensure_categorias_sistema()

        # 5. Enviar email de bienvenida (HTML + plain text fallback)
        #
        # Render del template HTML con branding Miniddo (teal). Mandamos
        # ambas versiones — clientes modernos muestran HTML, clientes
        # plain-text caen al fallback.
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives

        ctx = {
            "nombre_director": data["nombres_director"],
            "nombre_jardin": tenant.nombre,
            "url": data["dominio"],
            "usuario": data["email_director"],
            "password": password,
        }
        subject = f"Bienvenida/o a Miniddo · {tenant.nombre}"
        text_body = (
            f"Hola {data['nombres_director']},\n\n"
            f"El jardín {tenant.nombre} ya está disponible en Miniddo.\n\n"
            f"URL: https://{data['dominio']}\n"
            f"Usuario: {data['email_director']}\n"
            f"Contraseña: {password}\n\n"
            f"Por seguridad, te recomendamos cambiar tu contraseña al ingresar.\n\n"
            f"Gracias por ser parte de Miniddo.\n"
            f"— Una aplicación de COREM LABS"
        )
        html_body = render_to_string("email/welcome_jardin.html", ctx)

        logger.info(
            "Preparando envio de email de bienvenida: from=%s to=%s subject=%s backend=%s",
            settings.DEFAULT_FROM_EMAIL,
            data["email_director"],
            subject,
            settings.EMAIL_BACKEND,
        )
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[data["email_director"]],
            )
            msg.attach_alternative(html_body, "text/html")
            sent_count = msg.send(fail_silently=False)
            logger.info(
                "Email de bienvenida enviado OK: to=%s sent_count=%s",
                data["email_director"], sent_count,
            )
        except Exception as e:
            logger.exception(
                "Error al enviar email de bienvenida a %s: %s",
                data["email_director"], e,
            )
            # NO re-raise: el tenant ya esta creado. Si el email falla, el
            # SUPERADMIN puede ver la pass en los logs y mandarla manual.

        return tenant


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ()
    search_fields = ("domain", "tenant__nombre")
    autocomplete_fields = ("tenant",)
