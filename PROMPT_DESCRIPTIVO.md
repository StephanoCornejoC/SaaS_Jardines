# Proyecto: SAAS COREM - Sistema de Gestion para Jardines de Infancia

## Que necesito

Construir un SaaS completo para administrar jardines de infancia (kinders) en Peru. Mi empresa COREM Labs vende este sistema a jardines. El primer cliente piloto es "Jardin Garabato".

El sistema tiene dos partes:
1. **Panel web para el jardin** (React): lo usan la directora, secretaria y profesores para su operacion diaria
2. **Panel de administracion para COREM** (Django Admin): lo uso yo para gestionar todos los jardines clientes, crear cuentas, monitorear, etc.

Cada jardin es independiente. Los datos de un jardin nunca se mezclan con los de otro. Esto se logra con django-tenants (multi-tenant por schema en PostgreSQL).

---

## El negocio: como funciona un jardin de infancia

Un jardin de infancia atiende ninos de 2 a 5 años. Los niños se dividen en aulas por edad: los de 2 años en un aula, los de 3 en otra, etc. Cada aula tiene un profesor titular y opcionalmente un auxiliar.

### Ciclo anual del jardin:

**Inicio de año (marzo):**
- Los padres matriculan a sus hijos. La matricula tiene un costo unico.
- Se asigna cada niño a su aula segun la edad.
- Se configura la pension mensual de cada alumno (puede variar por alumno).
- Se registran los datos del niño: DNI, fecha de nacimiento, apoderados (papa, mama, tutor), ficha medica (alergias, tipo de sangre, seguro, contacto de emergencia).

**Durante el año (marzo a diciembre):**
- Cada mes, los padres pagan la pension. El pago puede ser en efectivo, Yape, Plin o transferencia.
- La secretaria registra los pagos manualmente y puede generar un QR para que el padre pague por Yape/Plin.
- El jardin envia comunicados a los padres (avisos generales o por aula) via email.
- Se registran los gastos del jardin: sueldos de profesores, servicios (luz, agua, internet), materiales educativos, gastos facturados, etc.
- La directora puede ver el flujo de caja: cuanto entro, cuanto salio, cual es el balance.
- Al final de cada mes se puede hacer un cierre contable.
- El sistema siempre debe estar sincronizado a la fecha actual para que los pagos y demás esté sincronizado.

**Fin de año (diciembre):**
- Los ninos de 2 pasan a 3, los de 3 a 4, los de 4 a 5.
- Los de 5 anos se graduan y pasan a estado "egresado".
- Los egresados se mantienen en el sistema por 1 año (por si necesitan constancias) y luego se eliminan sus datos junto con sus pagos para evitar sobrecostos.
- Cada fin de año, se descargará un pdf con todos los registros de pagos, matriculas, alumnos y demás datos importantes para que el usuario y yo como proveedor pueda tener respaldo de todo lo que se hizo, por si en algún momento quieren revisarlo o lo necesiten 

---

## Modulos del sistema

### 1. Gestion de Jardines (solo COREM)
Yo como COREM creo y administro los jardines clientes desde el Django Admin. Cada jardin tiene: nombre, RUC, direccion, telefono, email, logo, y un plan (estandar, que puede ser variable). Puedo suspender un jardin si deja de pagar.

### 2. Usuarios y Roles
El sistema maneja 2 roles jerarquicos:
- **SUPERADMIN**: yo (COREM), acceso total a todo
- **ADMIN_JARDIN**: el dueno/administrador del jardin, acceso total a su jardin y administra todo su jardín desde el sistema, menos modificacones que afecten directamente al saas, el SaaS debe ser seguro para que los usuarios no lo dañen.


La autenticacion es por usuario + contrasena (con tokens JWT) que yo como COREM también voy a generar y administrar.

### 3. Alumnos
Ficha completa del alumno con:
- Datos basicos: DNI, nombres, apellidos, fecha de nacimiento, genero, foto
- Apoderados: uno o varios (padre, madre, tutor), cada uno con DNI, telefono y email
- Ficha medica: tipo de sangre, alergias, seguro medico, hospital de referencia, contacto de emergencia
- Asignacion a un aula
- Estado: activo, retirado o egresado (los retirados también permaneceran el el sistema pero solo por un año, luego serán eliminados completamente.)

### 4. Profesores
Datos del profesor. Cada profesor tiene contratos (tiempo completo, medio tiempo, por horas) con un sueldo definido. Cada mes se registra el pago al profesor.

### 5. Aulas
Aulas divididas por nivel de edad (2, 3, 4, 5 anos). Cada una con capacidad maxima(definida por el admin), profesor titular y auxiliar (opcional) asignado. El sistema muestra cuantos alumnos hay vs la capacidad.

### 6. Matriculas
Proceso anual. Cada alumno se matricula en un aula con un costo. Estado: pendiente, pagada o anulada.

### 7. Pensiones (modulo financiero principal)
Cada alumno tiene una pension mensual configurable (puede ser diferente por alumno si hay becas o descuentos). Cada mes se genera un registro de pago por alumno con fecha de vencimiento.

La secretaria puede:
- Ver todos los pagos pendientes, pagados y vencidos
- Registrar un pago (marcar como pagado, indicar metodo)
- Generar un codigo QR con los datos del pago para que el padre pague por Yape/Plin
- Ver un reporte de morosidad (quien debe y cuanto)

**Muy importante:** cuando se registra un pago, automaticamente se crea un ingreso en el flujo de caja.

### 8. Flujo de Caja
Control financiero completo:
- Ingresos: matriculas, pensiones (se crean automaticamente al registrar pagos)
- Egresos: sueldos, servicios, materiales (se registran manualmente)
- Categorias configurables
- Balance mensual y anual
- Cierre contable mensual (una vez cerrado, no se modifica)

### 9. Asistencia
El profesor selecciona su aula y la fecha, y aparece la lista de todos los alumnos. Marca cada uno como presente, ausente, tardanza o justificado. Se guarda todo de una sola vez. Si un alumno falta 3 o mas dias seguidos, se envia un email automatico al apoderado.

### 10. Comunicaciones
El jardin envia comunicados a los padres. Puede ser general (a todos) o por aula especifica. Al enviarlo, se manda un email automatico a los apoderados relevantes.

### 11. Dashboard
Pantalla principal con 4 indicadores clave:
- Total de alumnos activos
- Total de profesores
- Ingresos del mes actual
- Porcentaje de morosidad

Mas un grafico de barras con los ingresos mensuales del año.

### 12. Reportes
4 reportes descargables en Excel:
- Reporte de morosidad (pagos pendientes y vencidos)
- Lista completa de alumnos con datos de contacto
- Reporte de asistencia por aula y mes
- Reporte de caja con ingresos y egresos

### 13. Migracion Academica
Proceso anual de promocion:
- Vista previa: muestra que pasara (cuantos suben de nivel, cuantos se graduan)
- Ejecucion: promueve a todos los alumnos al siguiente nivel
- Limpieza: despues de 1 año, elimina todos los datos (pagos, matriculas, ficha, TODO) datos de egresados

### 14. Notificaciones automaticas (en segundo plano)
- Recordatorio de pago 3 dias antes del vencimiento (email al apoderado)
- Alerta cuando un alumno falta 3+ dias seguidos
- Calculo diario de metricas del dashboard

---

## Stack tecnologico

- **Backend:** Django 5 + Django REST Framework + django-tenants + SimpleJWT + Celery + Redis
- **Frontend:** React 18 + Vite + Ant Design + Zustand + Chart.js
- **Base de datos:** PostgreSQL 16
- **Admin theme:** django-jazzmin (NO django-unfold, tiene bugs con Python moderno)
- **PDFs:** xhtml2pdf (NO weasyprint, es muy pesado para Railway)
- **Excel:** openpyxl
- **QR codes:** qrcode + Pillow
- **Deploy:** Backend en Railway.app (~$5-7/mes), Frontend en Vercel (gratis)

---

## Seguridad (muy importante, hay datos de menores)

- Autenticacion JWT con tokens que rotan y se invalidan al cambiar contrasena
- Proteccion contra fuerza bruta: 5 intentos fallidos = bloqueo 15 minutos
- Rate limiting en la API
- Permisos estrictos por rol
- URL del admin ofuscada (no /admin/)
- Archivos de alumnos protegidos con autenticacion (no accesibles sin login)
- Registro de auditoria de todos los cambios (quien cambio que y cuando)
- Datos de egresados se eliminan fisicamente después de un año
- CORS restrictivo en produccion

---

## Panel de administracion COREM (Django Admin)

Desde el Django Admin yo gestiono:
- **Jardines:** crear nuevos jardines clientes, asignar dominios, cambiar planes, suspender
- **Usuarios:** crear administradores para cada jardin, alumnos, padres, fichas, todo, resetear contrasenas
- **Monitoreo:** ver datos de cualquier jardin (alumnos, pagos, morosidad)
- **Auditoria:** revisar el log de quien hizo que en el sistema
- **Seguridad:** ver intentos de acceso fallidos, bloqueos

El admin debe tener iconos para cada seccion (FontAwesome via jazzmin) y estar organizado logicamente.

---

## Consideraciones de costo

El sistema se despliega en Railway que cobra por uso. Necesito que sea lo mas eficiente posible:
- Paginacion obligatoria en todos los listados (maximo 25 items por pagina)
- Usar select_related y prefetch_related en todas las consultas con relaciones
- Cache con Redis para las metricas del dashboard (se recalculan 1 vez al dia, no en cada visita)
- Las tareas pesadas (enviar emails, calcular metricas) van por Celery en segundo plano
- El frontend es un build estatico en Vercel (cero costo de compute)
- Imagenes comprimidas al subir
- Lazy loading de modulos React (code splitting por ruta)

---

## Como levantar en desarrollo

Necesito que el proyecto incluya:
- Entorno virtual Python con todas las dependencias
- Frontend con npm install y npm run dev
- Script o instrucciones para crear el tenant de prueba y los usuarios iniciales

**Credenciales iniciales:**
- Superadmin COREM: admin@corem.pe / Corem2026!
- Admin Jardin Garabato: admin@jardingarabato.pe / Garabato2026!

---

Construye todo el proyecto completo, funcional y listo para levantar. Incluye modelos, serializers, views, URLs, admin, factories, y el frontend con todas las paginas funcionales.
