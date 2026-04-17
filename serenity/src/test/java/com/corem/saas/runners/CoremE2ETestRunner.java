package com.corem.saas.runners;

import io.cucumber.junit.platform.engine.Constants;
import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

/**
 * Runner principal para todos los tests E2E de SAAS COREM.
 *
 * Ejecuta todos los feature files de la suite.
 * Usar: mvn verify -Dcucumber.filter.tags="@tag" para filtrar por tag.
 *
 * Tags disponibles:
 * - @autenticacion, @login, @logout, @validacion
 * - @alumnos, @crear-alumno, @editar-alumno, @buscar-alumno, @detalle-alumno
 * - @pensiones, @lista-pensiones, @filtrar-pensiones, @registrar-pago, @generar-qr
 * - @asistencia, @sin-aula, @seleccionar-aula, @guardar-asistencia
 * - @flujo-de-caja, @estadisticas-caja, @nueva-transaccion, @cierres-mensuales
 * - @dashboard, @kpis, @grafico
 * - @comunicaciones, @crear-comunicacion, @enviar-comunicacion
 * - @reportes, @descargar-excel
 * - @navegacion, @menu-lateral, @ruta-privada-sin-sesion
 *
 * Smoke test: @tc-auth-01 OR @tc-dash-01 OR @tc-stu-01
 */
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = Constants.GLUE_PROPERTY_NAME, value = "com.corem.saas.stepdefinitions")
@ConfigurationParameter(key = Constants.PLUGIN_PROPERTY_NAME,
    value = "pretty," +
            "html:target/cucumber-reports/report.html," +
            "json:target/cucumber-reports/cucumber.json," +
            "junit:target/cucumber-reports/cucumber.xml," +
            "io.cucumber.core.plugin.SerenityReporterParallel")
@ConfigurationParameter(key = Constants.FEATURES_PROPERTY_NAME, value = "src/test/resources/features")
@ConfigurationParameter(key = Constants.FILTER_TAGS_PROPERTY_NAME, value = "not @skip")
public class CoremE2ETestRunner {
    // Runner vacío: JUnit Platform Suite lo gestiona todo via las anotaciones
}
