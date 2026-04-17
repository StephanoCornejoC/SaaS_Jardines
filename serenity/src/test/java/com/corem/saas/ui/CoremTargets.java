package com.corem.saas.ui;

import net.serenitybdd.screenplay.targets.Target;

/**
 * Targets (selectores) para la UI de SAAS COREM (Ant Design 5).
 * Centraliza todos los locators del sistema. Siguiendo el principio DRY del Screenplay Pattern,
 * los targets no pertenecen a Page Objects sino que son constantes reutilizables.
 */
public class CoremTargets {

    private CoremTargets() {
        // Clase de constantes, no instanciar
    }

    // ============================================================
    // GENERICOS - Ant Design
    // ============================================================

    /** Toast de mensaje de Ant Design (message.success / message.error) */
    public static final Target ANT_MESSAGE_CONTENT =
        Target.the("mensaje de Ant Design").locatedBy(".ant-message-notice-content");

    /** Spinner de carga de Ant Design */
    public static final Target ANT_SPINNER =
        Target.the("spinner de carga").locatedBy(".ant-spin-spinning");

    /** Modal de Ant Design (activo) */
    public static final Target ANT_MODAL =
        Target.the("modal de Ant Design").locatedBy(".ant-modal-wrap:not([style*='display: none']) .ant-modal");

    /** Footer del modal activo */
    public static final Target ANT_MODAL_FOOTER =
        Target.the("footer del modal").locatedBy(".ant-modal-wrap:not([style*='display: none']) .ant-modal-footer");

    /** Boton primario del footer del modal */
    public static final Target ANT_MODAL_OK_BUTTON =
        Target.the("boton OK del modal").locatedBy(".ant-modal-wrap:not([style*='display: none']) .ant-modal-footer .ant-btn-primary");

    /** Boton cancelar/secundario del footer del modal */
    public static final Target ANT_MODAL_CANCEL_BUTTON =
        Target.the("boton Cancelar del modal").locatedBy(".ant-modal-wrap:not([style*='display: none']) .ant-modal-footer button:not(.ant-btn-primary)");

    /** Titulo del modal activo */
    public static final Target ANT_MODAL_TITLE =
        Target.the("titulo del modal").locatedBy(".ant-modal-wrap:not([style*='display: none']) .ant-modal-title");

    /** Dropdown de Select de Ant Design (visible) */
    public static final Target ANT_SELECT_DROPDOWN_VISIBLE =
        Target.the("dropdown de select visible").locatedBy(".ant-select-dropdown:not(.ant-select-dropdown-hidden)");

    /** Opciones en el dropdown de Select de Ant Design */
    public static Target antSelectOption(String optionTitle) {
        return Target.the("opcion '" + optionTitle + "' del select")
            .locatedBy(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item[title='" + optionTitle + "']");
    }

    /** Opcion en el dropdown por titulo parcial */
    public static Target antSelectOptionContaining(String text) {
        return Target.the("opcion del select que contiene '" + text + "'")
            .locatedBy(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option[title*='" + text + "']");
    }

    /** Popconfirm de Ant Design */
    public static final Target ANT_POPCONFIRM =
        Target.the("popconfirm de Ant Design").locatedBy(".ant-popconfirm");

    /** Boton OK del Popconfirm */
    public static final Target ANT_POPCONFIRM_OK =
        Target.the("boton OK del popconfirm").locatedBy(".ant-popconfirm .ant-btn-primary");

    /** Filas de la tabla de Ant Design */
    public static final Target ANT_TABLE_ROWS =
        Target.the("filas de la tabla").locatedBy(".ant-table-tbody tr.ant-table-row");

    /** Encabezados de la tabla de Ant Design */
    public static final Target ANT_TABLE_HEADERS =
        Target.the("encabezados de la tabla").locatedBy(".ant-table-thead th");

    /** Tags dentro de la tabla (estados) */
    public static final Target ANT_TABLE_TAGS =
        Target.the("tags de estado en la tabla").locatedBy(".ant-table-tbody .ant-tag");

    /** Menu lateral de Ant Design */
    public static final Target ANT_SIDER =
        Target.the("sidebar de Ant Design").locatedBy(".ant-layout-sider");

    /** Menu de Ant Design */
    public static final Target ANT_MENU =
        Target.the("menu lateral").locatedBy(".ant-menu");

    // ============================================================
    // LOGIN
    // ============================================================

    public static final Target LOGIN_EMAIL_INPUT =
        Target.the("campo de email en login").locatedBy("input[type='email'], input#email, input[placeholder*='correo'], input[placeholder*='email']");

    public static final Target LOGIN_PASSWORD_INPUT =
        Target.the("campo de contrasena en login").locatedBy("input[type='password']");

    public static final Target LOGIN_SUBMIT_BUTTON =
        Target.the("boton de ingresar").locatedBy("button[type='submit'], .ant-btn-primary[type='submit']");

    public static final Target LOGIN_CARD_TITLE =
        Target.the("titulo de la tarjeta de login").locatedBy(".ant-card-head-title, h2, .login-title");

    // ============================================================
    // HEADER / NAVEGACION SUPERIOR
    // ============================================================

    public static final Target HEADER_EMAIL =
        Target.the("email del usuario en el header").locatedBy(".ant-layout-header *[class*='user'], .ant-layout-header");

    public static final Target HEADER_LOGOUT_BUTTON =
        Target.the("boton Salir").locatedBy(".ant-layout-header button, .ant-layout-header [role='button']");

    public static final Target HEADER_COLLAPSE_BUTTON =
        Target.the("boton de colapsar sidebar").locatedBy(".ant-layout-header button:first-child");

    // ============================================================
    // DASHBOARD
    // ============================================================

    public static final Target DASHBOARD_HEADING =
        Target.the("encabezado del dashboard").locatedBy("h1, h2, h3, h4").containingText("Dashboard");

    public static final Target DASHBOARD_CHART_CANVAS =
        Target.the("canvas del grafico de ingresos").locatedBy("canvas");

    public static final Target KPI_TOTAL_ALUMNOS =
        Target.the("KPI Total Alumnos").locatedBy(".ant-statistic").containingText("Alumnos");

    public static final Target KPI_TOTAL_PROFESORES =
        Target.the("KPI Total Profesores").locatedBy(".ant-statistic").containingText("Profesores");

    public static final Target KPI_INGRESOS_MES =
        Target.the("KPI Ingresos del Mes").locatedBy(".ant-statistic").containingText("Ingresos");

    public static final Target KPI_MOROSIDAD =
        Target.the("KPI Morosidad").locatedBy(".ant-statistic").containingText("Morosidad");

    public static final Target KPI_STATISTIC_VALUE =
        Target.the("valor del KPI").locatedBy(".ant-statistic-content-value");

    // ============================================================
    // ALUMNOS
    // ============================================================

    public static final Target ALUMNOS_HEADING =
        Target.the("encabezado de Alumnos").locatedBy("h1, h2, h3, h4").containingText("Alumnos");

    public static final Target ALUMNOS_TABLE =
        Target.the("tabla de alumnos").locatedBy(".ant-table-wrapper");

    public static final Target ALUMNOS_NEW_BUTTON =
        Target.the("boton Nuevo Alumno").locatedBy("button").containingText("Nuevo Alumno");

    public static final Target ALUMNOS_SEARCH_INPUT =
        Target.the("campo de busqueda de alumnos").locatedBy("input[placeholder*='Buscar'], input[placeholder*='buscar'], input[placeholder*='Search']");

    public static final Target ALUMNO_FORM_DNI =
        Target.the("campo DNI del formulario").locatedBy(".ant-modal input[placeholder*='DNI'], .ant-modal input#dni, .ant-modal #alumnoForm_dni");

    public static final Target ALUMNO_FORM_NOMBRES =
        Target.the("campo Nombres del formulario").locatedBy(".ant-modal input[placeholder*='Nombres'], .ant-modal input#nombres, .ant-modal #alumnoForm_nombres");

    public static final Target ALUMNO_FORM_APELLIDOS =
        Target.the("campo Apellidos del formulario").locatedBy(".ant-modal input[placeholder*='Apellidos'], .ant-modal input#apellidos, .ant-modal #alumnoForm_apellidos");

    public static final Target ALUMNO_FORM_FECHA_NACIMIENTO =
        Target.the("campo Fecha de Nacimiento").locatedBy(".ant-modal .ant-picker input");

    public static final Target ALUMNO_FORM_GENERO =
        Target.the("select de Genero en el formulario").locatedBy(".ant-modal .ant-form-item:has(label:contains('Genero')) .ant-select");

    // ============================================================
    // PENSIONES
    // ============================================================

    public static final Target PENSIONES_HEADING =
        Target.the("encabezado de Pensiones").locatedBy("h1, h2, h3, h4").containingText("Pensiones");

    public static final Target PENSIONES_TABLE =
        Target.the("tabla de pensiones").locatedBy(".ant-table-wrapper");

    public static final Target PENSIONES_FILTER_MES =
        Target.the("filtro de Mes").locatedBy(".ant-select:nth-of-type(1)");

    public static final Target PENSIONES_FILTER_ANIO =
        Target.the("filtro de Anio").locatedBy(".ant-select:nth-of-type(2)");

    public static final Target PENSIONES_FILTER_ESTADO =
        Target.the("filtro de Estado").locatedBy(".ant-select:nth-of-type(3)");

    public static final Target PAGO_MODAL =
        Target.the("modal de Registrar Pago").locatedBy(".ant-modal").containingText("Registrar Pago");

    public static final Target PAGO_MONTO_INPUT =
        Target.the("campo de monto del pago").locatedBy(".ant-modal input[type='number'], .ant-modal .ant-input-number-input");

    public static final Target QR_MODAL =
        Target.the("modal de QR").locatedBy(".ant-modal-confirm, .ant-modal").containingText("QR");

    public static final Target QR_IMAGE =
        Target.the("imagen del codigo QR").locatedBy(".ant-modal img, .ant-modal canvas");

    // ============================================================
    // ASISTENCIA
    // ============================================================

    public static final Target ASISTENCIA_HEADING =
        Target.the("encabezado de Asistencia").locatedBy("h1, h2, h3, h4").containingText("Asistencia");

    public static final Target ASISTENCIA_AULA_SELECT =
        Target.the("selector de aula en asistencia").locatedBy(".ant-select:first-of-type");

    public static final Target ASISTENCIA_DATE_PICKER =
        Target.the("selector de fecha en asistencia").locatedBy(".ant-picker");

    public static final Target ASISTENCIA_SAVE_BUTTON =
        Target.the("boton guardar asistencia").locatedBy("button").containingText("Guardar");

    // ============================================================
    // CAJA (CASHFLOW)
    // ============================================================

    public static final Target CAJA_STAT_INGRESOS =
        Target.the("card de Ingresos").locatedBy(".ant-statistic, .ant-card").containingText("Ingreso");

    public static final Target CAJA_STAT_EGRESOS =
        Target.the("card de Egresos").locatedBy(".ant-statistic, .ant-card").containingText("Egreso");

    public static final Target CAJA_STAT_BALANCE =
        Target.the("card de Balance").locatedBy(".ant-statistic, .ant-card").containingText("Balance");

    public static final Target CAJA_TAB_TRANSACCIONES =
        Target.the("tab Transacciones").locatedBy(".ant-tabs-tab").containingText("Transacciones");

    public static final Target CAJA_TAB_CIERRES =
        Target.the("tab Cierres Mensuales").locatedBy(".ant-tabs-tab").containingText("Cierres");

    public static final Target CAJA_NUEVA_TRANSACCION_BUTTON =
        Target.the("boton Nueva Transaccion").locatedBy("button").containingText("Nueva Transaccion");

    public static final Target CAJA_CLOSURES_TABLE =
        Target.the("tabla de cierres mensuales").locatedBy(".ant-tabs-tabpane-active .ant-table-wrapper");

    public static final Target CAJA_TRANSACTION_TABLE =
        Target.the("tabla de transacciones").locatedBy(".ant-table-wrapper");

    // ============================================================
    // COMUNICACIONES
    // ============================================================

    public static final Target COMUNICACIONES_HEADING =
        Target.the("encabezado de Comunicaciones").locatedBy("h1, h2, h3, h4").containingText("Comunicaciones");

    public static final Target COMUNICACIONES_TABLE =
        Target.the("tabla de comunicaciones").locatedBy(".ant-table-wrapper");

    public static final Target COMUNICACIONES_NEW_BUTTON =
        Target.the("boton Nueva Comunicacion").locatedBy("button").containingText("Nueva Comunicacion");

    public static final Target COMUNICACION_TITULO_INPUT =
        Target.the("campo Titulo de la comunicacion").locatedBy(".ant-modal input[placeholder*='Titulo'], .ant-modal input#titulo");

    public static final Target COMUNICACION_CONTENIDO_INPUT =
        Target.the("campo Contenido de la comunicacion").locatedBy(".ant-modal textarea");

    public static final Target COMUNICACION_TIPO_SELECT =
        Target.the("selector de Tipo de comunicacion").locatedBy(".ant-modal .ant-select:first-of-type");

    public static final Target COMUNICACION_AULA_FORM_ITEM =
        Target.the("campo Aula en el formulario").locatedBy(".ant-modal .ant-form-item").containingText("Aula");

    // ============================================================
    // REPORTES
    // ============================================================

    public static final Target REPORTES_HEADING =
        Target.the("encabezado de Reportes").locatedBy("h1, h2, h3, h4").containingText("Reportes");

    public static final Target REPORTES_DOWNLOAD_BUTTONS =
        Target.the("botones de Descargar Excel").locatedBy("button").containingText("Descargar Excel");
}
