// Generador del Manual Comercial SAAS COREM + Tabla de Precios
// Uso: node generate_manual.js

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  TabStopType, TabStopPosition, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak
} = require("docx");

// ======= Estilos reutilizables =======
const COLOR_PRIMARY = "1890FF";    // Azul corporativo (mismo del frontend)
const COLOR_ACCENT  = "722ED1";    // Morado acento
const COLOR_SUCCESS = "52C41A";    // Verde
const COLOR_WARNING = "FAAD14";    // Amarillo
const COLOR_DARK    = "1F1F1F";
const COLOR_MUTED   = "595959";
const COLOR_LIGHT   = "F0F5FF";

const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: "D9D9D9" };
const allBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };

// ======= Helpers =======
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    ...opts,
    children: [new TextRun({ text, ...(opts.run || {}) })],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, color: COLOR_PRIMARY, size: 36 })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, color: COLOR_DARK, size: 28 })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, color: COLOR_ACCENT, size: 24 })],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22 })],
  });
}

function bulletBold(boldPart, rest, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { after: 80 },
    children: [
      new TextRun({ text: boldPart, bold: true, size: 22 }),
      new TextRun({ text: rest, size: 22 }),
    ],
  });
}

function cell(text, opts = {}) {
  const { bold = false, color = COLOR_DARK, bg = null, align = AlignmentType.LEFT, width = 2340 } = opts;
  return new TableCell({
    borders: allBorders,
    width: { size: width, type: WidthType.DXA },
    shading: bg ? { fill: bg, type: ShadingType.CLEAR } : undefined,
    margins: { top: 120, bottom: 120, left: 160, right: 160 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold, color, size: 22 })],
    })],
  });
}

function headerCell(text, width = 2340) {
  return new TableCell({
    borders: allBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: { top: 140, bottom: 140, left: 160, right: 160 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 22 })],
    })],
  });
}

// ======= PORTADA =======
const portada = [
  new Paragraph({ spacing: { before: 1800 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "COREM", bold: true, size: 88, color: COLOR_PRIMARY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
    children: [new TextRun({ text: "Labs S.A.C.", size: 32, color: COLOR_MUTED })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
    children: [new TextRun({ text: "Manual Comercial", bold: true, size: 56, color: COLOR_DARK })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 800 },
    children: [new TextRun({ text: "SAAS COREM — Gestión de Jardines de Infancia", size: 30, italics: true, color: COLOR_MUTED })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: "Piloto: Jardín Garabato", size: 26, color: COLOR_ACCENT, bold: true })],
  }),
  new Paragraph({ spacing: { before: 2400 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Documento de entrenamiento y ventas", size: 22, color: COLOR_MUTED, italics: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Abril 2026 — Lima, Perú", size: 22, color: COLOR_MUTED })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ======= ÍNDICE (manual, no automático) =======
const indice = [
  h1("Índice"),
  p("1. Presentación del producto", { spacing: { after: 80 } }),
  p("2. ¿A quién va dirigido?", { spacing: { after: 80 } }),
  p("3. Problema que resolvemos", { spacing: { after: 80 } }),
  p("4. Propuesta de valor", { spacing: { after: 80 } }),
  p("5. Módulos del sistema (13 en total)", { spacing: { after: 80 } }),
  p("6. Flujo típico de trabajo diario", { spacing: { after: 80 } }),
  p("7. Seguridad y confiabilidad", { spacing: { after: 80 } }),
  p("8. Ventajas competitivas", { spacing: { after: 80 } }),
  p("9. Planes y precios (tarifa plana)", { spacing: { after: 80 } }),
  p("10. Comparativo de planes", { spacing: { after: 80 } }),
  p("11. Preguntas frecuentes del cliente", { spacing: { after: 80 } }),
  p("12. Guion de ventas sugerido", { spacing: { after: 80 } }),
  p("13. Proceso de incorporación (onboarding)", { spacing: { after: 80 } }),
  p("14. Contacto", { spacing: { after: 80 } }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ======= 1. PRESENTACIÓN =======
const presentacion = [
  h1("1. Presentación del producto"),
  p(
    "SAAS COREM es un sistema integral en la nube diseñado específicamente para la gestión administrativa de jardines de infancia en el Perú. Digitaliza los procesos de matrícula, pensiones, asistencia, comunicaciones con padres, flujo de caja y reportes, todo desde una sola plataforma accesible por cualquier navegador web."
  ),
  p(
    "Nuestra piloto es el Jardín Garabato, con quien hemos validado cada módulo durante el proceso de desarrollo para garantizar que resuelva los problemas reales del día a día."
  ),
  h3("En una frase"),
  new Paragraph({
    spacing: { before: 120, after: 240 },
    border: { left: { style: BorderStyle.SINGLE, size: 24, color: COLOR_PRIMARY, space: 12 } },
    indent: { left: 360 },
    children: [new TextRun({
      text: "\u201CDejamos de usar cuadernos, Excel y WhatsApp disperso. Todo el jardín funciona desde una sola aplicación, segura y profesional.\u201D",
      italics: true, size: 26, color: COLOR_DARK,
    })],
  }),
];

// ======= 2. A QUIÉN VA DIRIGIDO =======
const aQuien = [
  h1("2. ¿A quién va dirigido?"),
  p(
    "Jardines de infancia privados en el Perú con entre 20 y 150 alumnos, que hoy gestionan su administración de forma manual o con herramientas dispersas (cuadernos físicos, hojas de Excel sueltas, grupos de WhatsApp) y buscan ordenar y profesionalizar sus operaciones sin invertir en software costoso."
  ),
  h3("Usuario directo del sistema"),
  p(
    "SAAS COREM está diseñado para ser utilizado exclusivamente por la dueña o la directora del jardín. Ella es la única persona que opera el sistema con su propio usuario administrador, y gestiona desde ahí toda la administración del jardín."
  ),
  p(
    "Este enfoque de un único usuario responde a tres criterios de diseño:"
  ),
  bulletBold("Control total y responsabilidad clara: ", "la dueña o directora sabe exactamente qué se hizo, quién lo hizo y cuándo, porque es ella misma."),
  bulletBold("Seguridad de datos sensibles: ", "las fichas médicas, pagos y datos personales de los niños se manejan por una sola persona de confianza."),
  bulletBold("Simplicidad operativa: ", "no requiere capacitar a un equipo completo ni definir quién puede hacer qué. Un único usuario hace todo."),
  p(
    "Si el jardín desea que otra persona colabore puntualmente (por ejemplo, registrar pagos un día que la dueña no esté), comparte sus credenciales de forma temporal. Como el sistema solo permite una sesión activa a la vez, nunca habrá dos personas usando la plataforma al mismo tiempo, lo que garantiza la integridad y la trazabilidad de la información."
  ),
];

// ======= 3. PROBLEMA =======
const problema = [
  h1("3. Problema que resolvemos"),
  p("Un jardín típico en Lima enfrenta estos dolores operativos cada mes:"),
  bulletBold("Morosidad descontrolada: ", "no saben con exactitud cuántos padres deben y cuánto suma el total pendiente, porque el registro es manual."),
  bulletBold("Duplicación de trabajo: ", "anotan el pago en un cuaderno y luego lo vuelven a anotar en el libro de caja; errores y tiempo perdido."),
  bulletBold("Comunicación dispersa: ", "información crítica (suspensión de clases, alertas de inasistencia) se pierde en grupos de WhatsApp saturados."),
  bulletBold("Pérdida de tiempo en consultas: ", "cada vez que un padre pregunta algo, la secretaria busca entre carpetas físicas durante varios minutos."),
  bulletBold("Fichas médicas desactualizadas o inaccesibles: ", "en una emergencia, no encuentran rápido el tipo de sangre o las alergias del niño."),
  bulletBold("Reportes inexistentes: ", "cuando la dueña pide balance mensual, la secretaria debe sumar manualmente en calculadora."),
  bulletBold("Errores humanos costosos: ", "un pago mal registrado, una asistencia olvidada, una matrícula duplicada."),
];

// ======= 4. PROPUESTA DE VALOR =======
const propuesta = [
  h1("4. Propuesta de valor"),
  p("SAAS COREM convierte la administración caótica en un flujo ordenado, medible y profesional en menos de una semana:"),
  bulletBold("Todo integrado: ", "registras un pago y automáticamente se actualiza el flujo de caja, sin doble digitación."),
  bulletBold("Multi-tenant seguro: ", "los datos de tu jardín viven en su propio espacio aislado; ningún otro cliente puede verlos."),
  bulletBold("Responsivo en celular: ", "la secretaria puede registrar pagos desde su móvil si el padre viene al patio del jardín."),
  bulletBold("Costo predecible: ", "tarifa plana mensual, sin sorpresas por cantidad de transacciones ni por usuarios."),
  bulletBold("Sin instalación: ", "funciona en cualquier navegador moderno (Chrome, Edge, Firefox). Nada que descargar."),
  bulletBold("Actualizaciones automáticas: ", "nuevas funciones y mejoras de seguridad sin que tengas que hacer nada."),
  bulletBold("Respaldos automáticos: ", "la información se respalda diariamente. Si algo pasa, lo recuperamos."),
];

// ======= 5. MÓDULOS =======
const modulos = [
  h1("5. Módulos del sistema"),
  p("SAAS COREM incluye 13 módulos que cubren el 100 % de la operación administrativa de un jardín de infancia."),

  h3("5.1. Panel principal (Dashboard)"),
  p("Al ingresar se muestran cuatro indicadores clave: total de alumnos activos, total de profesores, ingresos del mes en soles y porcentaje de morosidad con semáforo de color. Incluye un gráfico de barras con los ingresos de los últimos 12 meses."),

  h3("5.2. Alumnos"),
  p("Registro completo por alumno: DNI, nombres, apellidos, fecha de nacimiento, género, aula asignada y estado (activo, retirado o egresado). La ficha de detalle incluye tres pestañas: información general, apoderados con sus teléfonos, y ficha médica con tipo de sangre, alergias, seguro y contacto de emergencia."),

  h3("5.3. Profesores"),
  p("Alta y baja de docentes con validación de email, especialidad, teléfono y estado activo. Pueden asignarse como titulares de un aula."),

  h3("5.4. Aulas"),
  p("Define cada aula con su nombre (por ejemplo, \u201CSala Azul\u201D), nivel de edad, capacidad máxima, profesor titular y cantidad actual de alumnos. El sistema alerta si se sobrepasa la capacidad."),

  h3("5.5. Matrículas"),
  p("Al crear una matrícula, el sistema genera automáticamente las diez pensiones mensuales del año escolar (marzo a diciembre), con sus fechas de vencimiento. Filtrable por año y estado."),

  h3("5.6. Pensiones"),
  p("Registro de pagos con cuatro métodos aceptados: efectivo, transferencia, Yape y Plin. Al marcar un pago como pagado, se crea automáticamente la transacción de ingreso en el flujo de caja. Incluye generación de código QR único por pensión para mostrar al padre."),

  h3("5.7. Flujo de caja"),
  p("Tres indicadores superiores (ingresos del mes, egresos del mes y balance) con código de color. Lista detallada de transacciones por categoría (pensiones, matrícula, material, planilla, servicios, otros) con filtros por mes y año. Incluye una pestaña de cierres mensuales para congelar los totales."),

  h3("5.8. Asistencia"),
  p("Registro masivo por aula y fecha. La profesora elige el aula y marca cada alumno como presente, ausente, con tardanza o justificado. El backend valida que los alumnos pertenezcan al aula. Alertas automáticas por email al apoderado si un alumno acumula 3 o más inasistencias consecutivas."),

  h3("5.9. Comunicaciones"),
  p("Envío de comunicados por correo electrónico a todos los padres (tipo GENERAL) o solo a los de un aula específica (tipo POR AULA). Estado del mensaje en borrador o enviado, con registro de quién y cuándo lo envió."),

  h3("5.10. Reportes"),
  p("Cuatro reportes descargables en formato Excel con un solo clic: morosidad (pagos vencidos), lista de alumnos activos, asistencia por aula y mes, y flujo de caja del período. Cada archivo incluye encabezados con color, bordes y totales calculados."),

  h3("5.11. Migración académica"),
  p("Al final del año escolar, un solo proceso promueve a todos los alumnos al siguiente nivel y genera las matrículas del año siguiente. Incluye vista previa antes de ejecutar y registro histórico de cada migración ejecutada."),

  h3("5.12. Usuario administrador único"),
  p("El sistema contempla un único usuario administrador por jardín, operado normalmente por la dueña o la directora. Este usuario tiene acceso completo a todos los módulos. Por política de seguridad, solo se permite una sesión activa a la vez: si se inicia sesión desde otro navegador o dispositivo, la sesión anterior se cierra automáticamente, evitando accesos concurrentes no autorizados."),

  h3("5.13. Notificaciones automáticas"),
  p("El sistema envía correos automáticos en dos casos: recordatorio de pensión por vencer (tres días antes) y alerta de inasistencias consecutivas. Sin costo adicional."),
];

// ======= 6. FLUJO TÍPICO =======
const flujo = [
  h1("6. Flujo típico de trabajo diario"),
  p("Un día completo de trabajo de la directora en aproximadamente tres minutos de interacción con el sistema:"),
  bulletBold("07:45 a.m. — ", "Abre la aplicación. Revisa en el dashboard que ayer ingresaron S/. 1,200."),
  bulletBold("08:00 a.m. — ", "Registra la asistencia de las tres aulas en 5 minutos."),
  bulletBold("10:30 a.m. — ", "Llega un padre a pagar pensión. Lo busca, registra el pago con Yape, le muestra el QR. Un minuto."),
  bulletBold("11:00 a.m. — ", "Una madre pregunta por la alergia de su hija. Entra a ficha médica. 20 segundos."),
  bulletBold("02:00 p.m. — ", "Redacta comunicado por feriado del lunes. Lo envía a los 50 padres. 30 segundos."),
  bulletBold("04:00 p.m. — ", "Anota el pago a la profesora de inglés como egreso."),
  bulletBold("05:30 p.m. — ", "Descarga el reporte de morosidad del mes y lo guarda para la reunión con su contadora."),
  bulletBold("05:40 p.m. — ", "Cierra sesión. Todo queda auditado, sin papeles."),
];

// ======= 7. SEGURIDAD =======
const seguridad = [
  h1("7. Seguridad y confiabilidad"),
  p("La seguridad de los datos de los niños es innegociable. SAAS COREM implementa por defecto:"),
  bulletBold("Autenticación con JWT: ", "sesiones firmadas que expiran cada 30 minutos y se renuevan automáticamente mientras la persona está trabajando."),
  bulletBold("Sesión única garantizada: ", "solo se permite una sesión activa por usuario. Si alguien intenta ingresar con las mismas credenciales desde otro dispositivo, la sesión anterior se cierra automáticamente. Esto previene accesos simultáneos no autorizados y le avisa de inmediato a la directora si sus credenciales fueron usadas en otro lado."),
  bulletBold("Protección anti fuerza bruta: ", "tras 5 intentos fallidos de login, el usuario se bloquea 15 minutos."),
  bulletBold("Aislamiento multi-tenant: ", "cada jardín tiene su propio esquema en PostgreSQL. Ningún dato se cruza entre clientes."),
  bulletBold("HTTPS obligatorio: ", "toda comunicación entre el navegador y el servidor está cifrada."),
  bulletBold("Log de auditoría: ", "queda registrado cada creación, modificación o eliminación de registro, con fecha y hora exactas."),
  bulletBold("Respaldos diarios automáticos: ", "copia de seguridad todos los días, con retención según el plan contratado."),
  bulletBold("Cumplimiento OWASP Top 10: ", "protección contra las 10 vulnerabilidades web más comunes del mundo."),
  bulletBold("Confirmación obligatoria: ", "cualquier eliminación pide confirmación antes de ejecutar. Nunca se pierde información por un clic accidental."),
];

// ======= 8. VENTAJAS =======
const ventajas = [
  h1("8. Ventajas competitivas"),
  bulletBold("Hecho en Perú, para Perú: ", "en español peruano, con moneda S/., zona horaria Lima, y soporte nativo para Yape y Plin."),
  bulletBold("Sin comisión por transacción: ", "otros sistemas cobran un porcentaje por cada pago procesado. Nosotros no."),
  bulletBold("Tarifa plana predecible: ", "sabes exactamente cuánto pagarás cada mes, sin importar cuántos alumnos o pagos manejes dentro de tu plan."),
  bulletBold("Soporte humano: ", "atención personalizada por WhatsApp y email. No somos un call center."),
  bulletBold("Rápida implementación: ", "el jardín empieza a operar en la plataforma en menos de una semana."),
  bulletBold("Exportación total: ", "todos tus datos en Excel cuando quieras. Tú eres el dueño de la información."),
  bulletBold("Actualizaciones gratuitas: ", "las mejoras y nuevas funciones se incluyen sin costo adicional."),
];

// ======= 9. PLANES Y PRECIOS =======
const planes = [
  h1("9. Planes y precios"),
  p(
    "Nuestro modelo es de tarifa plana mensual. Sin comisiones por transacción, sin cobros por usuario adicional, sin costos ocultos. El precio depende únicamente del tamaño del jardín medido por alumnos activos."
  ),
  p({
    text: "Todos los precios están expresados en soles peruanos (S/.) e incluyen el hosting en la nube, respaldos, actualizaciones y soporte.",
  }),

  h3("Tabla de planes tarifa plana"),

  // Tabla principal de precios
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2340, 2340, 2340, 2340],
    rows: [
      // Encabezado
      new TableRow({
        tableHeader: true,
        children: [
          headerCell("Característica", 2340),
          headerCell("Básico", 2340),
          headerCell("Profesional", 2340),
          headerCell("Premium", 2340),
        ],
      }),
      // Precio
      new TableRow({
        children: [
          cell("Precio mensual", { bold: true, bg: COLOR_LIGHT }),
          cell("S/. 199", { bold: true, align: AlignmentType.CENTER, color: COLOR_DARK }),
          cell("S/. 299", { bold: true, align: AlignmentType.CENTER, color: COLOR_SUCCESS }),
          cell("S/. 499", { bold: true, align: AlignmentType.CENTER, color: COLOR_ACCENT }),
        ],
      }),
      new TableRow({
        children: [
          cell("Precio anual (15 % descuento)", { bold: true, bg: COLOR_LIGHT }),
          cell("S/. 2,029", { align: AlignmentType.CENTER }),
          cell("S/. 3,049", { align: AlignmentType.CENTER }),
          cell("S/. 5,089", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Alumnos activos", { bold: true, bg: COLOR_LIGHT }),
          cell("Hasta 30", { align: AlignmentType.CENTER }),
          cell("Hasta 80", { align: AlignmentType.CENTER }),
          cell("Ilimitados", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Usuario administrador", { bold: true, bg: COLOR_LIGHT }),
          cell("1 (dueña/directora)", { align: AlignmentType.CENTER }),
          cell("1 (dueña/directora)", { align: AlignmentType.CENTER }),
          cell("1 (dueña/directora)", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Sesión única activa", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Aulas", { bold: true, bg: COLOR_LIGHT }),
          cell("Hasta 3", { align: AlignmentType.CENTER }),
          cell("Hasta 6", { align: AlignmentType.CENTER }),
          cell("Ilimitadas", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Dashboard con KPIs", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("CRUD alumnos, aulas, profesores", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Pensiones y caja", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("QR de pago Yape y Plin", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Asistencia masiva", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Reportes Excel (4 tipos)", { bold: true, bg: COLOR_LIGHT }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Comunicaciones por email", { bold: true, bg: COLOR_LIGHT }),
          cell("Hasta 200/mes", { align: AlignmentType.CENTER }),
          cell("Hasta 800/mes", { align: AlignmentType.CENTER }),
          cell("Ilimitadas", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Alertas automáticas de asistencia", { bold: true, bg: COLOR_LIGHT }),
          cell("—", { align: AlignmentType.CENTER, color: COLOR_MUTED }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Migración académica anual", { bold: true, bg: COLOR_LIGHT }),
          cell("—", { align: AlignmentType.CENTER, color: COLOR_MUTED }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Cierres mensuales de caja", { bold: true, bg: COLOR_LIGHT }),
          cell("—", { align: AlignmentType.CENTER, color: COLOR_MUTED }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("✓", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
        ],
      }),
      new TableRow({
        children: [
          cell("Respaldos automáticos", { bold: true, bg: COLOR_LIGHT }),
          cell("Diarios, 7 días", { align: AlignmentType.CENTER }),
          cell("Diarios, 30 días", { align: AlignmentType.CENTER }),
          cell("Diarios, 90 días", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Soporte", { bold: true, bg: COLOR_LIGHT }),
          cell("Email, 48 h", { align: AlignmentType.CENTER }),
          cell("Email y WhatsApp, 24 h", { align: AlignmentType.CENTER }),
          cell("WhatsApp prioritario, 4 h", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Onboarding y capacitación", { bold: true, bg: COLOR_LIGHT }),
          cell("Videos auto-servicio", { align: AlignmentType.CENTER }),
          cell("Sesión online 1 hora", { align: AlignmentType.CENTER }),
          cell("Sesión presencial 2 horas", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Subdominio personalizado", { bold: true, bg: COLOR_LIGHT }),
          cell("mijardin.corem.pe", { align: AlignmentType.CENTER }),
          cell("mijardin.corem.pe", { align: AlignmentType.CENTER }),
          cell("Dominio propio", { align: AlignmentType.CENTER }),
        ],
      }),
    ],
  }),

  new Paragraph({ spacing: { before: 240 } }),

  h3("Detalle de cada plan"),

  new Paragraph({
    spacing: { before: 120, after: 80 },
    children: [new TextRun({ text: "Plan Básico — S/. 199 / mes", bold: true, size: 24, color: COLOR_PRIMARY })],
  }),
  p("Ideal para jardines pequeños o recién formados con hasta 30 alumnos. Cubre toda la operación esencial: matrículas, pensiones, caja, asistencia y reportes. Perfecto para reemplazar Excel y cuadernos. Un solo usuario administrador operado por la dueña o directora, con sesión única activa."),

  new Paragraph({
    spacing: { before: 120, after: 80 },
    children: [
      new TextRun({ text: "Plan Profesional — S/. 299 / mes", bold: true, size: 24, color: COLOR_SUCCESS }),
      new TextRun({ text: "   (recomendado)", italics: true, size: 22, color: COLOR_MUTED }),
    ],
  }),
  p("El plan más popular. Para jardines medianos con 30 a 80 alumnos que necesitan funcionalidades avanzadas: alertas automáticas, migración académica, cierres contables mensuales y soporte por WhatsApp. El 80 % de nuestros clientes elige este plan."),

  new Paragraph({
    spacing: { before: 120, after: 80 },
    children: [new TextRun({ text: "Plan Premium — S/. 499 / mes", bold: true, size: 24, color: COLOR_ACCENT })],
  }),
  p("Para jardines grandes con más de 80 alumnos o que manejan múltiples sedes. Incluye dominio propio (por ejemplo, app.tujardin.com), soporte prioritario por WhatsApp con respuesta en 4 horas, y sesión de capacitación presencial en Lima."),

  new Paragraph({ children: [new PageBreak()] }),
];

// ======= 10. COMPARATIVO =======
const comparativo = [
  h1("10. Comparativo con alternativas"),
  p("¿Por qué SAAS COREM y no la competencia o las herramientas manuales?"),

  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2340, 2340, 2340, 2340],
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          headerCell("Factor", 2340),
          headerCell("SAAS COREM", 2340),
          headerCell("Excel y WhatsApp", 2340),
          headerCell("Software genérico", 2340),
        ],
      }),
      new TableRow({
        children: [
          cell("Costo mensual", { bold: true, bg: COLOR_LIGHT }),
          cell("S/. 199 a S/. 499", { align: AlignmentType.CENTER, bold: true, color: COLOR_SUCCESS }),
          cell("S/. 0 pero mucho tiempo", { align: AlignmentType.CENTER }),
          cell("S/. 500 a S/. 1,500+", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Ahorro de tiempo", { bold: true, bg: COLOR_LIGHT }),
          cell("15 a 20 horas/mes", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("Cero", { align: AlignmentType.CENTER }),
          cell("10 a 15 horas/mes", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Adaptado a jardines PE", { bold: true, bg: COLOR_LIGHT }),
          cell("Sí, 100 %", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("No", { align: AlignmentType.CENTER }),
          cell("Rara vez", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Yape y Plin integrado", { bold: true, bg: COLOR_LIGHT }),
          cell("Sí", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("No", { align: AlignmentType.CENTER }),
          cell("No", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Reportes automáticos", { bold: true, bg: COLOR_LIGHT }),
          cell("Un clic", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("Manuales", { align: AlignmentType.CENTER }),
          cell("Configurables", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Respaldo de datos", { bold: true, bg: COLOR_LIGHT }),
          cell("Automático diario", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("Ninguno o manual", { align: AlignmentType.CENTER }),
          cell("Según proveedor", { align: AlignmentType.CENTER }),
        ],
      }),
      new TableRow({
        children: [
          cell("Soporte en español", { bold: true, bg: COLOR_LIGHT }),
          cell("Sí, peruano", { align: AlignmentType.CENTER, color: COLOR_SUCCESS, bold: true }),
          cell("No aplica", { align: AlignmentType.CENTER }),
          cell("A veces en inglés", { align: AlignmentType.CENTER }),
        ],
      }),
    ],
  }),

  new Paragraph({ spacing: { before: 240 } }),

  h3("Retorno de inversión"),
  p(
    "Un jardín con 50 alumnos pagando S/. 350 de pensión factura aproximadamente S/. 17,500 al mes. El plan Profesional a S/. 299 representa el 1.7 % de esos ingresos. Sólo con reducir la morosidad en 2 % (recuperando S/. 350 de un alumno moroso) el sistema ya se paga solo."
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ======= 11. FAQs =======
const faqs = [
  h1("11. Preguntas frecuentes del cliente"),

  h3("¿Quién usa el sistema en el día a día?"),
  p("Exclusivamente la dueña o la directora del jardín, con su propio usuario administrador. Así se mantiene control total sobre la información sensible (fichas médicas, pagos, datos personales de los niños) sin necesidad de definir permisos para cada colaborador."),

  h3("¿Y si quiero que otra persona me ayude a registrar pagos?"),
  p("Puede prestar sus credenciales de forma puntual. Como el sistema solo permite una sesión activa a la vez, si la otra persona inicia sesión, la suya se cerrará automáticamente, evitando conflictos. Para colaboración simultánea permanente, evalúe con nosotros un plan personalizado."),

  h3("¿Qué significa que solo hay una sesión activa?"),
  p("Si la directora inicia sesión desde la computadora del jardín y luego intenta ingresar desde su celular, la sesión de la computadora se cerrará automáticamente. Esto tiene dos beneficios: primero, evita el uso simultáneo descontrolado de la cuenta, y segundo, actúa como alerta si alguien ajeno intenta usar sus credenciales (ella lo nota porque se cierra su sesión)."),

  h3("¿Qué pasa si necesito más alumnos que los del plan?"),
  p("Sube al siguiente plan sin penalidad. Si por ejemplo crece de 25 a 40 alumnos, migra del Básico al Profesional y paga la diferencia a partir del mes siguiente, sin costo de cambio."),

  h3("¿Puedo cancelar cuando quiera?"),
  p("Sí. Sin contratos forzosos ni penalidades. Avisas con un mes de anticipación y exportas toda tu información en Excel."),

  h3("¿Los padres necesitan instalar una aplicación?"),
  p("No. Los padres no interactúan con la plataforma directamente. El jardín es quien usa el sistema, y la comunicación con los padres es por email o presencial como siempre."),

  h3("¿Funciona sin internet?"),
  p("SAAS COREM requiere internet para funcionar porque está en la nube. Sin embargo, si hay una caída puntual, puedes seguir operando con papel y luego digitalizar. Nuestros servidores tienen 99.9 % de disponibilidad."),

  h3("¿Mis datos están seguros?"),
  p("Absolutamente. Los datos viven en servidores con certificación internacional, cifrados en reposo y en tránsito. Nadie del equipo COREM accede a tus datos sin tu autorización expresa."),

  h3("¿Cuánto tiempo tarda la implementación?"),
  p("Tres a cinco días hábiles. Un día para crear tu cuenta, otro para cargar tus alumnos y profesores iniciales (lo hacemos nosotros desde tu Excel si quieres), y el resto para capacitar al personal."),

  h3("¿Hay descuentos?"),
  p("Sí. Al pagar el año completo por adelantado se aplica un 15 % de descuento (dos meses gratis). Si refieres a otro jardín que contrate, ambos reciben un mes gratis."),

  h3("¿Pueden integrar módulos específicos para mi jardín?"),
  p("Para personalizaciones grandes tenemos planes a medida. Para ajustes menores (campos adicionales, reportes personalizados) lo evaluamos sin costo en muchos casos."),

  new Paragraph({ children: [new PageBreak()] }),
];

// ======= 12. GUION DE VENTAS =======
const guion = [
  h1("12. Guion de ventas sugerido"),
  p("Estructura recomendada para una reunión de 30 minutos con el dueño o directora del jardín:"),

  h3("Minutos 0 a 3 — Rompe-hielo y calificación"),
  bullet("Saludo y presentación personal."),
  bullet("Pregunta clave: \u201C¿cómo llevan hoy la administración del jardín?\u201D"),
  bullet("Pregunta clave: \u201C¿cuánto tiempo les toma generar el reporte de morosidad?\u201D"),
  bullet("Escuchar atentamente. Anotar sus dolores."),

  h3("Minutos 3 a 8 — Problema y propuesta de valor"),
  bullet("Resumir sus dolores con sus propias palabras: \u201CO sea, están perdiendo tiempo en X, Y, Z.\u201D"),
  bullet("Introducir SAAS COREM: \u201CEsto es exactamente lo que resolvemos.\u201D"),
  bullet("Mencionar piloto con Jardín Garabato como prueba social."),

  h3("Minutos 8 a 20 — Demo guiada"),
  bullet("Login en vivo con cuenta demo."),
  bullet("Mostrar dashboard: KPIs, gráfico."),
  bullet("Mostrar flujo de pago: buscar alumno, registrar con Yape, generar QR."),
  bullet("Mostrar reporte de morosidad: descarga en Excel en un clic."),
  bullet("Mostrar asistencia masiva."),
  bullet("Mostrar alerta automática: \u201Ceste email le llega solo al apoderado, sin que hagan nada.\u201D"),
  bullet("Resaltar: \u201Custed es la única que entra al sistema, con un usuario a su nombre. Nadie más tiene acceso.\u201D"),
  bullet("Demostrar sesión única: abrir dos pestañas, iniciar sesión en la segunda, mostrar que la primera se cerró."),

  h3("Minutos 20 a 25 — Precios y siguiente paso"),
  bullet("Presentar la tabla de tres planes."),
  bullet("Recomendar el Profesional por defecto. Ajustar al Básico si el jardín es pequeño."),
  bullet("Enfatizar: sin contratos forzosos, cancelable cuando quieran."),
  bullet("Mencionar retorno de inversión: \u201Cse paga solo con recuperar uno o dos pagos morosos.\u201D"),

  h3("Minutos 25 a 30 — Cierre"),
  bullet("Preguntar: \u201C¿qué dudas le quedan?\u201D"),
  bullet("Ofrecer mes de prueba gratuito para facilitar el sí."),
  bullet("Agendar la sesión de onboarding para la siguiente semana."),
  bullet("Enviar resumen por WhatsApp en los siguientes 30 minutos."),

  new Paragraph({ children: [new PageBreak()] }),
];

// ======= 13. ONBOARDING =======
const onboarding = [
  h1("13. Proceso de incorporación (onboarding)"),
  p("Así incorporamos a un nuevo jardín. Proceso típico de 3 a 5 días hábiles:"),

  h3("Día 1 — Alta técnica"),
  bullet("Creamos el espacio privado del jardín (tenant) con su propio subdominio."),
  bullet("Creamos el usuario administrador principal y le enviamos credenciales por WhatsApp."),
  bullet("Cargamos el logo del jardín si nos lo envían."),

  h3("Día 2 — Carga inicial de datos"),
  bullet("Ellos nos envían un Excel con alumnos, profesores y aulas actuales (o nosotros les damos una plantilla)."),
  bullet("Cargamos los datos en el sistema por ellos, sin costo adicional."),
  bullet("Crearemos las matrículas del año en curso para que las pensiones mensuales se generen automáticamente."),

  h3("Día 3 — Capacitación de la administradora"),
  bullet("Sesión online de 1 hora (plan Profesional) o presencial de 2 horas (plan Premium)."),
  bullet("Entrenamos directamente a la dueña o directora, quien será la única operadora del sistema."),
  bullet("Entregamos el manual de usuario final (diferente a este manual comercial)."),
  bullet("Le explicamos cómo funciona la sesión única y qué hacer si la sesión se cierra inesperadamente."),

  h3("Día 4 y 5 — Acompañamiento"),
  bullet("WhatsApp abierto para dudas."),
  bullet("Revisión a los 7 días de operación: ¿qué funciona? ¿qué mejorar?"),
  bullet("Optimizaciones sugeridas sin costo."),

  h3("Mes 2 en adelante — Operación estable"),
  bullet("Contacto mensual para resolver dudas y recibir feedback."),
  bullet("Envío de novedades y nuevas funciones lanzadas."),
];

// ======= 14. CONTACTO =======
const contacto = [
  h1("14. Contacto"),
  p("Para cerrar una venta, agendar una demo o resolver dudas:"),
  bulletBold("Empresa: ", "COREM Labs S.A.C."),
  bulletBold("Email comercial: ", "ventas@corem.pe"),
  bulletBold("Email técnico: ", "soporte@corem.pe"),
  bulletBold("WhatsApp comercial: ", "+51 999 999 999 (reemplazar con número real)"),
  bulletBold("Sitio web: ", "www.corem.pe"),
  bulletBold("Ciudad: ", "Lima, Perú"),

  new Paragraph({ spacing: { before: 480 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "— Fin del manual —", italics: true, color: COLOR_MUTED, size: 22 })],
  }),
];

// ======= DOCUMENTO =======
const doc = new Document({
  creator: "COREM Labs S.A.C.",
  title: "Manual Comercial SAAS COREM",
  description: "Manual de ventas para SAAS COREM con tabla de precios tentativos",
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Calibri", color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Calibri", color: COLOR_DARK },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Calibri", color: COLOR_ACCENT },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "SAAS COREM — Manual Comercial", size: 18, color: COLOR_MUTED, italics: true })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "COREM Labs S.A.C. — Página ", size: 18, color: COLOR_MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: COLOR_MUTED }),
          ],
        })],
      }),
    },
    children: [
      ...portada,
      ...indice,
      ...presentacion,
      ...aQuien,
      ...problema,
      ...propuesta,
      ...modulos,
      ...flujo,
      ...seguridad,
      ...ventajas,
      ...planes,
      ...comparativo,
      ...faqs,
      ...guion,
      ...onboarding,
      ...contacto,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  // Genera con timestamp si el anterior está abierto en Word
  let out = path.resolve(__dirname, "Manual_Comercial_SAAS_COREM.docx");
  try {
    fs.writeFileSync(out, buf);
  } catch (e) {
    if (e.code === "EBUSY") {
      const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 16);
      out = path.resolve(__dirname, `Manual_Comercial_SAAS_COREM_${ts}.docx`);
      fs.writeFileSync(out, buf);
      console.log("WARN: archivo original bloqueado, genero con timestamp");
    } else {
      throw e;
    }
  }
  console.log("OK:", out);
}).catch((err) => {
  console.error("ERROR:", err);
  process.exit(1);
});
