/**
 * Genera el Word "Guia de instalacion SAAS COREM" paso a paso
 * orientado a personas sin conocimientos tecnicos.
 */
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  BorderStyle,
  WidthType,
  ShadingType,
  PageNumber,
  Header,
  Footer,
  LevelFormat,
  convertInchesToTwip,
} = require("docx");
const fs = require("fs");
const path = require("path");

// ------------------ COLORES ------------------
const PRIMARY = "1677ff";
const DARK = "003a8c";
const BG_LIGHT = "e6f4ff";
const BG_WARN = "fff7e6";
const BG_OK = "f6ffed";
const TEXT_MUTED = "595959";

// ------------------ HELPERS ------------------
const h1 = (t) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 480, after: 240 },
    children: [new TextRun({ text: t, bold: true, size: 36, color: DARK })],
  });

const h2 = (t) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 320, after: 120 },
    children: [new TextRun({ text: t, bold: true, size: 28, color: PRIMARY })],
  });

const h3 = (t) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 100 },
    children: [new TextRun({ text: t, bold: true, size: 24, color: DARK })],
  });

const p = (t, opts = {}) =>
  new Paragraph({
    spacing: { before: 80, after: 120 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text: t, size: 22 })],
  });

const step = (num, title, desc) =>
  [
    new Paragraph({
      spacing: { before: 200, after: 80 },
      children: [
        new TextRun({
          text: `Paso ${num}. `,
          bold: true,
          size: 26,
          color: PRIMARY,
        }),
        new TextRun({ text: title, bold: true, size: 26, color: DARK }),
      ],
    }),
    new Paragraph({
      spacing: { before: 40, after: 100 },
      alignment: AlignmentType.JUSTIFIED,
      children: [new TextRun({ text: desc, size: 22 })],
    }),
  ];

const bullet = (t) =>
  new Paragraph({
    bullet: { level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: t, size: 22 })],
  });

const boldBullet = (b, rest) =>
  new Paragraph({
    bullet: { level: 0 },
    spacing: { before: 40, after: 40 },
    children: [
      new TextRun({ text: b, bold: true, size: 22 }),
      new TextRun({ text: rest, size: 22 }),
    ],
  });

// Cuadro resaltado con fondo (para tips, advertencias)
const calloutBox = (title, text, kind = "info") => {
  const bg = kind === "warn" ? BG_WARN : kind === "ok" ? BG_OK : BG_LIGHT;
  const titleColor = kind === "warn" ? "ad4e00" : kind === "ok" ? "389e0d" : DARK;
  const icon = kind === "warn" ? "IMPORTANTE" : kind === "ok" ? "CONSEJO" : "NOTA";

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: titleColor },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: titleColor },
      left: { style: BorderStyle.SINGLE, size: 8, color: titleColor },
      right: { style: BorderStyle.SINGLE, size: 2, color: titleColor },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: bg },
      insideVertical: { style: BorderStyle.NONE, size: 0, color: bg },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: bg },
            margins: { top: 140, bottom: 140, left: 200, right: 200 },
            children: [
              new Paragraph({
                spacing: { after: 80 },
                children: [
                  new TextRun({
                    text: `${icon}: `,
                    bold: true,
                    color: titleColor,
                    size: 22,
                  }),
                  new TextRun({ text: title, bold: true, size: 22 }),
                ],
              }),
              new Paragraph({
                children: [new TextRun({ text, size: 22 })],
              }),
            ],
          }),
        ],
      }),
    ],
  });
};

// Caja con codigo/comando
const codeBox = (text) =>
  new Paragraph({
    spacing: { before: 80, after: 120 },
    shading: { type: ShadingType.CLEAR, fill: "f5f5f5" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "d9d9d9" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "d9d9d9" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "d9d9d9" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "d9d9d9" },
    },
    children: [new TextRun({ text, font: "Consolas", size: 20 })],
  });

// ------------------ CONTENIDO ------------------

// Portada
const portada = [
  new Paragraph({
    spacing: { before: 2400, after: 200 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "GUIA DE", bold: true, size: 48, color: PRIMARY }),
    ],
  }),
  new Paragraph({
    spacing: { after: 200 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "INSTALACION", bold: true, size: 72, color: DARK }),
    ],
  }),
  new Paragraph({
    spacing: { after: 600 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "Paso a paso, sin complicaciones",
        italics: true,
        size: 28,
        color: TEXT_MUTED,
      }),
    ],
  }),
  new Paragraph({
    spacing: { after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "SAAS COREM", bold: true, size: 40 })],
  }),
  new Paragraph({
    spacing: { after: 3200 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "Sistema de gestion para jardines de infancia",
        size: 24,
        color: TEXT_MUTED,
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "Version del documento: Abril 2026",
        size: 18,
        color: TEXT_MUTED,
        italics: true,
      }),
    ],
  }),
  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Introduccion
const intro = [
  h1("Antes de empezar"),
  p(
    "Este documento la guiara paso a paso para instalar el sistema SAAS COREM en su computadora. No necesita conocimientos tecnicos. Los unicos requisitos son: tener una computadora con Windows 10 u 11, tener conexion a internet durante la instalacion, y paciencia (todo el proceso tarda entre 10 y 20 minutos la primera vez)."
  ),

  h2("Lo que el sistema va a hacer por usted"),
  boldBullet("Instalar Python: ", "un programa que hace funcionar la logica interna (no se preocupe por que es)."),
  boldBullet("Instalar Node.js: ", "otro programa que hace funcionar la pagina web del sistema."),
  boldBullet("Instalar PostgreSQL: ", "una base de datos donde se guarda toda la informacion (alumnos, pagos, etc.)."),
  boldBullet("Crear la estructura de datos: ", "prepara las tablas donde se almacenan las cosas."),
  boldBullet("Cargar datos de ejemplo: ", "algunos alumnos y aulas de prueba para que vea como funciona."),

  calloutBox(
    "Todo esto se hace automaticamente.",
    "Usted solo tiene que hacer unos clics y esperar. Si aparece una ventana azul preguntando si permite cambios, siempre diga SI.",
    "ok"
  ),

  h2("Que necesita tener listo antes de empezar"),
  bullet("Una computadora con Windows 10 o Windows 11."),
  bullet("Aproximadamente 2 GB de espacio libre en disco (va a tener 2 GB?, no se preocupe, es mas que suficiente)."),
  bullet("Conexion a internet estable (necesaria solo durante la instalacion)."),
  bullet("El paquete ZIP del sistema que le entregaron (o la carpeta descomprimida)."),
  bullet("Unos 20 minutos sin interrupciones."),

  calloutBox(
    "Si su Windows es muy viejo",
    "Si su Windows es anterior a Windows 10, el sistema no podra instalarse. Consulte con su proveedor COREM para ver alternativas.",
    "warn"
  ),
  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Parte 1: Primera instalacion
const parte1 = [
  h1("PARTE 1 - Primera instalacion"),
  p(
    "Esta parte la hace UNA SOLA VEZ, la primera vez que va a usar el sistema. Tarda entre 10 y 20 minutos. Despues de terminada, no la vuelve a hacer mas."
  ),

  ...step(
    "1",
    "Descomprimir el paquete",
    "Localice el archivo ZIP que le entregaron. Por lo general se llama algo como \"SAAS_COREM_INSTALADOR.zip\". Haga clic derecho sobre el y seleccione \"Extraer todo\" (o \"Extract All\"). Elija como destino una carpeta sencilla, por ejemplo su Escritorio. Espere a que termine de descomprimir."
  ),

  calloutBox(
    "Donde guardar la carpeta",
    "Le recomendamos guardarla en el Escritorio o en la carpeta Documentos. Evite carpetas con tildes, espacios raros o rutas muy largas (por ejemplo, no la ponga dentro de \"Onedrive\\\\Mis documentos - 2026\\\\Nuevo folder\").",
    "info"
  ),

  ...step(
    "2",
    "Abrir la carpeta descomprimida",
    "Dentro de la carpeta que acaba de descomprimir deberia ver estos archivos:"
  ),
  bullet("LEEME_PRIMERO.txt"),
  bullet("GUIA_DE_INSTALACION.docx (este documento)"),
  bullet("1_INSTALAR.bat"),
  bullet("2_INICIAR.bat"),
  bullet("3_DETENER.bat"),
  bullet("Una subcarpeta llamada \"codigo\""),

  ...step(
    "3",
    "Ejecutar el instalador COMO ADMINISTRADOR",
    "Localice el archivo 1_INSTALAR.bat. Haga CLIC DERECHO sobre el (no doble clic). En el menu que aparece, seleccione \"Ejecutar como administrador\"."
  ),

  calloutBox(
    "Por que administrador?",
    "Porque el instalador necesita permisos especiales para instalar PostgreSQL y Python en la computadora. Sin esos permisos no puede hacerlo. Es seguro.",
    "info"
  ),

  ...step(
    "4",
    "Aceptar los permisos de Windows",
    "Aparecera una ventana azul de Windows preguntando \"Desea permitir que esta aplicacion realice cambios en el dispositivo?\". Haga clic en SI."
  ),

  ...step(
    "5",
    "Esperar",
    "Se abrira una ventana negra con texto verde. Empezara a mostrar mensajes como \"Paso 1/5 - Instalando Python...\", \"Paso 2/5 - Instalando Node.js...\", etc. NO CIERRE esa ventana. Puede aparentar que esta congelada por unos minutos; es normal, esta descargando e instalando."
  ),

  calloutBox(
    "Puede tardar MUCHO",
    "La instalacion puede tardar hasta 20 minutos si su internet es lento. Si ve que no pasa nada por mucho tiempo, tenga paciencia. NO cierre la ventana.",
    "warn"
  ),

  ...step(
    "6",
    "Confirmar que termino bien",
    "Cuando la instalacion termine correctamente, vera en verde un mensaje grande que dice:"
  ),
  codeBox("INSTALACION COMPLETADA CON EXITO"),
  p(
    "Ademas el texto le dira cual es la contrasena para ingresar al sistema. Presione cualquier tecla para cerrar la ventana."
  ),

  calloutBox(
    "Y si algo fallo?",
    "Si en vez del mensaje de exito ve algun error en rojo, copie el texto del error (o tome una foto de la pantalla con el celular) y envielo al proveedor COREM. Ellos le ayudaran.",
    "warn"
  ),

  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Parte 2: Uso diario
const parte2 = [
  h1("PARTE 2 - Como usar el sistema cada dia"),
  p(
    "Una vez que hizo la instalacion inicial, usar el sistema es muy sencillo. Solo tiene que hacer clic en dos archivos."
  ),

  h2("Para abrir el sistema"),

  ...step(
    "1",
    "Hacer doble clic en 2_INICIAR.bat",
    "En la carpeta del sistema, localice el archivo 2_INICIAR.bat y haga DOBLE CLIC sobre el. Esta vez no hace falta \"como administrador\"."
  ),

  ...step(
    "2",
    "Esperar 20 segundos",
    "Se abrira una ventana negra que muestra el progreso (arrancando base de datos, arrancando servidor, arrancando interfaz). Cuando este listo, el navegador web (Chrome, Edge, Firefox) se abrira automaticamente con el sistema."
  ),

  ...step(
    "3",
    "Iniciar sesion",
    "Cuando vea la pantalla con el logo \"SAAS COREM\" y los campos para correo y contrasena, ingrese:"
  ),
  codeBox("Correo:     admin@garabato.com\nContrasena: Admin1234!"),
  p("Haga clic en el boton azul \"Iniciar Sesion\"."),

  calloutBox(
    "La primera vez cambie su contrasena",
    "Esa contrasena es solo para la primera vez. Apenas entre, le recomendamos cambiarla por una personal. (Esto se hace desde el boton de usuario arriba a la derecha).",
    "ok"
  ),

  h2("Mientras usa el sistema"),
  p(
    "Veras varias ventanas negras minimizadas en la barra de tareas con nombres como \"SAAS COREM - Backend\" y \"SAAS COREM - Frontend\". No las cierre. Ellas son lo que mantiene funcionando el sistema."
  ),
  p(
    "Si las cierra por error, solo tiene que volver a hacer doble clic en 2_INICIAR.bat para arrancarlas de nuevo."
  ),

  h2("Para apagar el sistema al final del dia"),

  ...step(
    "1",
    "Cerrar el navegador",
    "Cierre la pestana del navegador donde esta el sistema (o cierre el navegador completo)."
  ),

  ...step(
    "2",
    "Hacer doble clic en 3_DETENER.bat",
    "Esto apaga correctamente todos los servicios. Aparecera un mensaje rojo que dice \"SISTEMA DETENIDO\". Presione cualquier tecla para cerrar."
  ),

  calloutBox(
    "Es obligatorio apagar?",
    "No es obligatorio. Si no lo hace, el sistema sigue funcionando en segundo plano. Pero apagar cuando no lo usa libera memoria de la computadora y es buena practica.",
    "info"
  ),

  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Parte 3: Primeros pasos en el sistema
const parte3 = [
  h1("PARTE 3 - Primeros pasos dentro del sistema"),
  p(
    "Una vez que ingresa con su usuario, va a ver la pantalla principal del sistema. Aqui le explicamos brevemente que puede hacer. El manual comercial tiene el detalle completo; esto es solo para que se ubique."
  ),

  h2("Pantalla principal: el Dashboard"),
  p(
    "Es lo primero que ve. Tiene cuatro tarjetas grandes con los numeros importantes del jardin:"
  ),
  bullet("Total de alumnos activos"),
  bullet("Total de profesores activos"),
  bullet("Ingresos del mes en soles"),
  bullet("Porcentaje de morosidad (pagos pendientes)"),
  p(
    "Debajo tiene un grafico de barras con los ingresos de los ultimos 12 meses. Esto es todo lo que necesita ver cada manana para saber como va el jardin."
  ),

  h2("El menu lateral izquierdo"),
  p(
    "Desde ahi entra a los modulos principales:"
  ),
  boldBullet("Alumnos: ", "ver, crear, editar y eliminar alumnos. Tambien ver la ficha de cada uno."),
  boldBullet("Profesores: ", "gestionar al personal docente."),
  boldBullet("Aulas: ", "crear aulas (Sala Azul, Rojitos, etc.) y asignarles profesor titular."),
  boldBullet("Matriculas: ", "matricular alumnos para el ano escolar."),
  boldBullet("Pensiones: ", "ver los pagos del mes, registrar cobros, generar QR de Yape/Plin."),
  boldBullet("Flujo de Caja: ", "ingresos y egresos detallados del jardin."),
  boldBullet("Asistencia: ", "marcar asistencia diaria por aula."),
  boldBullet("Comunicaciones: ", "enviar avisos por email a todos los padres."),
  boldBullet("Reportes: ", "descargar reportes en Excel (morosidad, alumnos, asistencia, caja)."),
  boldBullet("Migracion: ", "promover alumnos al siguiente grado al final del ano."),

  h2("Cerrar sesion"),
  p(
    "Arriba a la derecha vera su correo y un boton \"Salir\". Al hacer clic cierra la sesion, y para volver a entrar tiene que iniciar sesion de nuevo."
  ),

  calloutBox(
    "Sesion unica",
    "Este sistema solo permite una sesion activa por usuario. Si usted esta conectada desde la computadora del jardin e intenta conectarse desde su celular, la sesion de la computadora se cerrara. Esto es para su seguridad.",
    "info"
  ),

  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Parte 4: Problemas comunes
const parte4 = [
  h1("PARTE 4 - Problemas comunes y como resolverlos"),

  h2("Al ejecutar 1_INSTALAR.bat me dice \"ERROR: debe ejecutarse como administrador\""),
  p(
    "Solucion: Cierre la ventana. Vuelva a la carpeta, haga CLIC DERECHO sobre 1_INSTALAR.bat (no doble clic), y seleccione \"Ejecutar como administrador\" en el menu que aparece."
  ),

  h2("Al ejecutar 1_INSTALAR.bat me dice \"su Windows no tiene winget\""),
  p(
    "Solucion: Actualice Windows. Vaya a Configuracion -> Windows Update -> Buscar actualizaciones. Instale todas las actualizaciones disponibles. Reinicie la computadora. Luego vuelva a ejecutar 1_INSTALAR.bat."
  ),

  h2("El instalador se queda mucho tiempo \"pegado\""),
  p(
    "Solucion: Tenga paciencia. Las descargas de Python, Node y PostgreSQL pueden tardar varios minutos en conexiones lentas. Si pasan mas de 30 minutos sin ningun mensaje nuevo, contacte a su proveedor."
  ),

  h2("Al ejecutar 2_INICIAR.bat, el navegador no se abre"),
  p(
    "Solucion: Abra el navegador manualmente y escriba en la barra de direcciones: "
  ),
  codeBox("http://localhost:3000"),
  p(
    "Si aparece la pantalla de login, todo esta bien. Si sigue sin aparecer, ejecute 3_DETENER.bat y luego 2_INICIAR.bat de nuevo."
  ),

  h2("Me aparece \"Credenciales incorrectas\" al intentar entrar"),
  p(
    "Solucion: Verifique que escribio correctamente (cuidado con mayusculas):"
  ),
  codeBox("admin@garabato.com\nAdmin1234!"),
  p(
    "La contrasena empieza con A mayuscula y termina con signo de admiracion."
  ),

  h2("Mi sesion se cerro sola"),
  p(
    "Puede pasar por dos motivos:"
  ),
  bullet("Pasaron mas de 30 minutos sin actividad. Normal, vuelva a entrar."),
  bullet("Alguien inicio sesion desde otro navegador o computadora con sus credenciales. Por politica de seguridad, solo se permite una sesion activa. Si no fue usted, cambie su contrasena."),

  h2("La computadora esta lenta cuando el sistema esta abierto"),
  p(
    "Solucion: Si no esta usando el sistema en ese momento, ejecute 3_DETENER.bat para liberarlo. Si necesita usarlo pero la maquina es muy vieja, consulte con su proveedor por una version mas liviana o un plan en la nube."
  ),

  new Paragraph({ children: [new TextRun({ text: "", size: 1 })], pageBreakBefore: true }),
];

// Cierre
const cierre = [
  h1("Ayuda y contacto"),
  p(
    "Si tiene cualquier duda, problema o sugerencia, comuniquese con su proveedor COREM. Estamos para ayudarla."
  ),
  p(""),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "COREM Labs S.A.C.", bold: true, size: 28, color: PRIMARY }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "Correo: scornejoc@bsginstitute.com", size: 22 }),
    ],
  }),
  p(""),
  p(""),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "- Gracias por confiar en SAAS COREM -",
        italics: true,
        color: TEXT_MUTED,
        size: 22,
      }),
    ],
  }),
];

// ------------------ DOCUMENTO ------------------
const doc = new Document({
  creator: "COREM Labs",
  title: "Guia de instalacion SAAS COREM",
  description: "Guia paso a paso de instalacion para usuarios no tecnicos",
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 22 },
        paragraph: { spacing: { line: 300 } },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "steps",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: {
              paragraph: { indent: { left: convertInchesToTwip(0.5), hanging: convertInchesToTwip(0.25) } },
            },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(0.8),
            bottom: convertInchesToTwip(0.8),
            left: convertInchesToTwip(0.9),
            right: convertInchesToTwip(0.9),
          },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({
                  text: "SAAS COREM - Guia de instalacion",
                  size: 18,
                  color: TEXT_MUTED,
                  italics: true,
                }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Pagina ", size: 18, color: TEXT_MUTED }),
                new TextRun({ children: [PageNumber.CURRENT], size: 18, color: TEXT_MUTED }),
                new TextRun({ text: " de ", size: 18, color: TEXT_MUTED }),
                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: TEXT_MUTED }),
              ],
            }),
          ],
        }),
      },
      children: [
        ...portada,
        ...intro,
        ...parte1,
        ...parte2,
        ...parte3,
        ...parte4,
        ...cierre,
      ],
    },
  ],
});

(async () => {
  try {
    const buffer = await Packer.toBuffer(doc);
    const outPath = path.resolve(
      __dirname,
      "..",
      "..",
      "..",
      "SAAS_COREM_INSTALADOR",
      "GUIA_DE_INSTALACION.docx"
    );
    fs.writeFileSync(outPath, buffer);
    console.log("OK: " + outPath);
    console.log("Tamano: " + (buffer.length / 1024).toFixed(1) + " KB");
  } catch (e) {
    console.error("ERROR: " + e.message);
    console.error(e.stack);
    process.exit(1);
  }
})();
