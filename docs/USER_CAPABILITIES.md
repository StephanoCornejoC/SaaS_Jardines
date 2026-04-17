# Capacidades del Usuario - SAAS COREM

Guia completa de lo que un usuario del sistema puede hacer, organizado por rol y modulo.

---

## Roles del sistema

| Rol | Descripcion | Acceso |
|-----|-------------|--------|
| **SUPERADMIN** | COREM interno (dueno del SaaS) | Todo + admin de tenants |
| **ADMIN_JARDIN** | Dueno o gerente del jardin | Todo dentro de su jardin |
| **DIRECTOR** | Director pedagogico | Gestion operativa completa |
| **SECRETARIA** | Administrativa | Alumnos, pagos, asistencia, matricula |
| **PROFESOR** | Docente del aula | Solo su aula: asistencia y consulta |

---

## Login y Sesion

Al ingresar a `https://garabato.tuapp.com` (subdominio por jardin):

- Login con email + contrasena
- Autenticacion JWT con refresh automatico (token dura 30 min, se renueva silenciosamente)
- Proteccion anti-brute-force (django-axes: 5 intentos fallidos bloquean 15 min)
- Mensajes de error diferenciados (red / credenciales / servidor)
- Cerrar sesion desde header superior derecho

---

## Dashboard principal

Al entrar ves:

- **4 KPIs en tarjetas**:
  - Total Alumnos activos
  - Total Profesores activos
  - Ingresos del Mes (S/.)
  - % Morosidad (rojo si >20%, amarillo si menor)
- **Grafico de barras**: Ingresos mensuales de los ultimos 12 meses

---

## Modulo Alumnos

### Lista de alumnos
- Tabla paginada (20 por pagina, configurable)
- Columnas: DNI, Nombres, Apellidos, Edad, Aula, Estado
- **Buscar** por nombre o DNI (enter para ejecutar)
- **Filtrar** por estado (ACTIVO, RETIRADO, EGRESADO)
- Badge de color segun estado

### Crear alumno
Modal con campos:
- DNI (8 digitos, requerido, unico)
- Nombres y Apellidos (requeridos)
- Fecha de Nacimiento (DatePicker DD/MM/YYYY)
- Genero (Masculino / Femenino)

### Editar alumno
Mismos campos del crear, precargados.

### Eliminar alumno
- **Popconfirm obligatorio** ("Esta seguro? Esta accion no se puede deshacer")
- Solo SUPERADMIN / ADMIN_JARDIN / DIRECTOR

### Ver detalle de alumno
Navegacion a `/alumnos/:id`:
- **Tab 1 - Informacion**: Datos personales, aula actual, estado, fecha ingreso
- **Tab 2 - Apoderados**: Lista de padres/tutores con telefono y relacion
- **Tab 3 - Ficha Medica**: Tipo de sangre, alergias, seguro, hospital, contacto emergencia

---

## Modulo Profesores

### Lista
- DNI, Nombres, Apellidos, Especialidad, Estado (activo / inactivo)
- Buscar por nombre o DNI

### Crear / Editar profesor
- DNI (requerido, unico)
- Nombres, Apellidos, Especialidad (requeridos)
- Telefono (opcional)
- **Email** con validacion (formato correcto)
- Switch Activo / Inactivo

### Eliminar profesor
- Popconfirm obligatorio

---

## Modulo Aulas

### Lista
- Nombre, Nivel (edad), Capacidad, Cantidad alumnos, Profesor titular, Estado

### Crear / Editar aula
- Nombre (ej. "Sala Azul", "Rojitos")
- Nivel (ej. "3 anios", "4 anios")
- Capacidad (1-50)
- Profesor titular (dropdown con profesores activos)
- Estado (ACTIVO / INACTIVO)

### Eliminar aula
- Popconfirm obligatorio

---

## Modulo Matriculas

### Lista
- Alumno, Aula, Ano Escolar, Costo mensual, Estado, Fecha matricula
- Filtrar por ano escolar (ultimos 5 anos)
- Filtrar por estado (ACTIVA, CANCELADA, FINALIZADA)

### Nueva matricula
- Alumno (dropdown buscable por DNI o nombre)
- Aula (dropdown con aulas activas)
- Ano escolar (2020-2040)
- Costo mensual (S/., min 0, step 50)

Al crear se generan automaticamente las pensiones mensuales del ano.

---

## Modulo Pensiones

### Lista
- Alumno, Mes, Ano, Monto, Estado, Fecha vencimiento, Fecha pago
- Filtrar por mes (Enero-Diciembre)
- Filtrar por ano
- Filtrar por estado (PENDIENTE / PAGADO / VENCIDO)
- Tag de color: PAGADO verde / VENCIDO rojo / PENDIENTE naranja

### Registrar pago
Solo SUPERADMIN / ADMIN_JARDIN / DIRECTOR. Modal con:
- Monto (prefilled con el monto esperado)
- Fecha de pago
- Metodo de pago (Efectivo / Transferencia / **Yape** / **Plin**)
- Observaciones (texto libre)

Al registrar:
- Se marca el pago como PAGADO
- Se crea **automaticamente** una transaccion de ingreso en el flujo de caja
- Se registra quien hizo el registro

### Generar QR de pago (Yape/Plin)
- Click en boton "QR" de cualquier pensiones pendiente
- Se abre modal con QR code personalizado
- Util para mostrar al padre en atencion presencial

### Reporte de morosidad
Endpoint `/morosidad` retorna pagos vencidos del periodo con total.

---

## Modulo Flujo de Caja

### Tarjetas KPI
- Ingresos del Mes (S/.) - verde con flecha arriba
- Egresos del Mes (S/.) - rojo con flecha abajo
- Balance - color dinamico segun signo

### Tab 1 - Transacciones
Tabla con todas las transacciones:
- Fecha, Categoria, Descripcion, Tipo (INGRESO verde / EGRESO rojo), Monto, Registrado por
- Filtrable por rango de fechas (`fecha_desde`, `fecha_hasta`)
- Filtrable por mes / ano
- **Validacion de inputs**: si pasas fecha invalida o mes >12, el sistema retorna 400 claro

### Crear transaccion
Modal con:
- Tipo (Ingreso / Egreso)
- Categoria (PENSION / MATRICULA / MATERIAL / PLANILLA / SERVICIOS / OTROS)
- Descripcion
- Monto (S/. min 0.01, 2 decimales)
- Fecha

### Tab 2 - Cierres Mensuales
Historial de cierres contables:
- Mes, Ano, Total Ingresos, Total Egresos, Balance, Estado, Fecha cierre

### Cerrar mes (ADMIN_JARDIN+)
Endpoint `/cerrar-mes` con mes+ano. Crea un registro `MonthlyClosure` que congela los totales.

---

## Modulo Asistencia

### Flujo diario
1. Selecciona un aula del dropdown
2. Selecciona la fecha (default: hoy)
3. El sistema carga automaticamente los alumnos del aula
4. Para cada alumno eliges estado:
   - Presente (default)
   - Ausente
   - Tardanza
   - Justificado
5. Click en "Guardar Asistencia"

El backend valida que los alumnos pertenezcan al aula (seguridad).

### Alertas automaticas
- Celery task corre diariamente
- Detecta alumnos con **3+ ausencias consecutivas**
- Envia email al apoderado principal con alerta
- Registrado en `EmailLog` para auditoria

---

## Modulo Comunicaciones

### Lista
- Titulo, Tipo (GENERAL / POR_AULA), Aula (si aplica), Estado (BORRADOR / ENVIADO), Fecha creacion, Creado por

### Crear comunicacion
Modal con:
- Titulo (requerido)
- Contenido (textarea)
- Tipo:
  - **GENERAL**: enviado a todos los padres del jardin
  - **POR_AULA**: solo padres del aula seleccionada (aparece campo condicional)

### Enviar comunicacion
- Popconfirm obligatorio
- Se envia por email a todos los apoderados correspondientes
- Registrado en `EmailLog`

---

## Modulo Reportes

Dashboard visual con 4 tarjetas clicables:

### 1. Reporte de Morosidad (Excel)
- Listado de pagos VENCIDOS
- Columnas: Alumno, DNI, Aula, Mes, Ano, Monto, Fecha Vencimiento, Dias Vencido
- Filtro por ano (obligatorio) y mes (opcional)

### 2. Lista de Alumnos (Excel)
- Listado completo con estado
- Columnas: Apellidos, Nombres, DNI, Fecha Nacimiento, Edad, Genero, Aula, Estado, Fecha Ingreso

### 3. Reporte de Asistencia (Excel)
- Por aula y mes
- Columnas: Alumno, Presentes, Ausentes, Tardanzas, Justificados, Total Dias, % Asistencia

### 4. Reporte de Caja (Excel)
- Ingresos y egresos del periodo
- Columnas: Fecha, Tipo, Categoria, Descripcion, Monto
- Totales finales: Total Ingresos, Total Egresos, Balance

**Todos los reportes:**
- Requieren rol ADMIN_JARDIN o superior
- Formato .xlsx con estilos y bordes
- Descarga directa al browser
- Loading state durante generacion

---

## Modulo Migracion Academica

Para promocionar alumnos al final del ano escolar.

### Vista Previa
Click "Vista Previa" para ver sin ejecutar:
- Que alumnos seran promovidos
- Que aulas se vaciaran
- Warnings (ej. alumnos sin aula asignada)

### Ejecutar Migracion
- **Doble Popconfirm** (es irreversible)
- Mueve alumnos activos al siguiente nivel
- Crea nuevas matriculas para el ano siguiente
- Marca alumnos mayores como EGRESADO

### Historial
Tabla de migraciones ejecutadas:
- ID, Fecha, Descripcion, Estado (EXITOSA / FALLIDA / EN_PROCESO), Registros procesados, Errores, Ejecutado por

---

## Seguridad y UX

### Proteccion de rutas
- Todas las rutas excepto `/login` requieren autenticacion
- Sin token valido redirige automaticamente a login
- Ruta desconocida redirige a `/dashboard`

### Manejo de errores
- **ErrorBoundary global** con boton "Recargar pagina" si algo crashea
- Mensajes toast de Ant Design para exitos/errores
- Errores de API muestran detalle del backend cuando disponible
- Timeout de 15s en requests (no se cuelgan)

### Acciones destructivas
Todo DELETE requiere confirmacion con Popconfirm:
- Texto claro del riesgo
- Boton "Si, eliminar" en rojo
- Boton "Cancelar" por defecto

### Responsive
- Sidebar colapsable automatica en pantallas <992px
- Tablas con scroll horizontal si no caben
- Grid adaptativo (xs 24 / sm 12 / lg 6 en KPIs)

---

## Panel admin (COREM interno)

URL: `https://backend.corem.pe/corem-panel-x9k2/` (URL ofuscada por seguridad)

Solo para SUPERADMIN:
- Gestion de tenants (jardines clientes)
- Crear nuevos jardines con schema aislado
- Crear usuarios del jardin
- Ver logs de auditoria de todos los modelos
- Administrar suscripciones

---

## Limites y notas operativas

- **Multi-tenancy**: cada jardin tiene su propio schema PostgreSQL. Los datos NUNCA se cruzan.
- **Rate limiting**: 20 req/min para anonimos, 100 req/min para autenticados
- **Paginacion DRF**: 25 items por defecto, configurable con `?page_size=50`
- **Idioma**: Todo en espanol (Peru, timezone America/Lima)
- **Moneda**: Soles peruanos (S/.) con 2 decimales exactos (Decimal, no float)
- **Pagos**: No hay pasarela. Registro manual + QR Yape/Plin (por decision de negocio)
- **Notificaciones**: Solo email (gratuito, via Gmail SMTP en produccion)
- **Backups**: Automaticos diarios via Railway PostgreSQL

---

## Que NO hace el sistema (decisiones de producto)

- No hay portal para padres (solo admin del jardin accede)
- No integracion con pasarelas de pago (Stripe, Culqi, etc.)
- No hay app movil nativa (solo web responsive)
- No chat en vivo ni videollamadas
- No gestion de evaluaciones academicas ni notas
- No SMS ni WhatsApp (solo email)
- No multi-idioma (solo espanol)
