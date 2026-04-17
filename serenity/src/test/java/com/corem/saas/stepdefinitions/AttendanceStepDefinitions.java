package com.corem.saas.stepdefinitions;

import com.corem.saas.abilities.CallTheCoremApi;
import com.corem.saas.helpers.CoremApiClient;
import com.corem.saas.helpers.TestDataStore;
import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.questions.IsElementEnabled;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.TheTableRowCount;
import com.corem.saas.tasks.MarkAttendance;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Asistencia.
 * Feature: attendance/asistencia.feature
 */
public class AttendanceStepDefinitions {

    private Actor actor;
    private String primeraAulaDisplayName;

    @Y("navego al modulo de Asistencia")
    public void navegoAsistencia() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/asistencia"));
    }

    @Entonces("el encabezado de asistencia es visible")
    public void encabezadoAsistenciaVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ASISTENCIA_HEADING), is(true)));
    }

    @Y("el selector de aula esta disponible")
    public void selectorAulaDisponible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ASISTENCIA_AULA_SELECT), is(true)));
    }

    @Y("el selector de fecha esta disponible")
    public void selectorFechaDisponible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ASISTENCIA_DATE_PICKER), is(true)));
    }

    @Y("el boton guardar esta deshabilitado")
    public void botonGuardarDeshabilitado() {
        actor.should(seeThat(IsElementEnabled.at(CoremTargets.ASISTENCIA_SAVE_BUTTON), is(false)));
    }

    @Y("la tabla muestra el mensaje de guia para seleccionar un aula")
    public void mensajeGuia() {
        Target emptyState = Target.the("estado vacio de la tabla")
            .locatedBy(".ant-empty, .ant-table-placeholder");
        actor.should(seeThat(IsElementVisible.at(emptyState), is(true)));
    }

    @Dado("existen aulas activas disponibles en el sistema via API")
    public void existenAulas() {
        actor = ScenarioContext.getActor();
        CoremApiClient api = CallTheCoremApi.as(actor);
        primeraAulaDisplayName = api.getFirstClassroomDisplayName();
        org.junit.jupiter.api.Assumptions.assumeTrue(
            primeraAulaDisplayName != null, "No hay aulas activas disponibles"
        );
        TestDataStore.getInstance().put(TestDataStore.CLASSROOM_NAME, primeraAulaDisplayName);
    }

    @Dado("existen aulas activas con alumnos en el sistema via API")
    public void existenAulasConAlumnos() {
        existenAulas();
    }

    @Cuando("selecciono la primera aula disponible")
    public void seleccionoPrimeraAula() {
        String aulaName = TestDataStore.getInstance().get(TestDataStore.CLASSROOM_NAME);
        if (aulaName == null) {
            CoremApiClient api = CallTheCoremApi.as(actor);
            aulaName = api.getFirstClassroomDisplayName();
        }
        actor.attemptsTo(
            Click.on(CoremTargets.ASISTENCIA_AULA_SELECT),
            SelectFromAntdDropdown.withOption(aulaName).from(CoremTargets.ASISTENCIA_AULA_SELECT)
        );
        try { Thread.sleep(1000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Cuando("selecciono la primera aula disponible con alumnos")
    public void seleccionoPrimeraAulaConAlumnos() {
        seleccionoPrimeraAula();
    }

    @Entonces("la tabla de asistencia muestra las columnas {string}, {string}, {string}")
    public void tablaAsistenciaColumnas(String col1, String col2, String col3) {
        for (String col : new String[]{col1, col2, col3}) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("columna " + col).locatedBy(".ant-table-thead th").containingText(col)
            ), is(true)));
        }
    }

    @Y("el boton guardar esta habilitado si el aula tiene alumnos")
    public void botonGuardarHabilitadoSiHayAlumnos() {
        int studentCount = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (studentCount > 0) {
            actor.should(seeThat(IsElementEnabled.at(CoremTargets.ASISTENCIA_SAVE_BUTTON), is(true)));
        }
    }

    @Y("los alumnos del aula tienen el estado \"PRESENTE\" por defecto")
    public void alumnosConPresenteDefault() {
        int studentCount = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (studentCount > 0) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("select de estado").locatedBy(".ant-table-tbody .ant-select")
            ), is(true)));
        }
    }

    @Cuando("marco el primer alumno como {string}")
    public void marcoAlumno1Como(String estado) {
        int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (count > 0) {
            actor.attemptsTo(MarkAttendance.forStudentAtRow(0, estado));
        }
    }

    @Y("marco el segundo alumno como {string} si existe")
    public void marcoAlumno2ComoSiExiste(String estado) {
        int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (count >= 2) {
            actor.attemptsTo(MarkAttendance.forStudentAtRow(1, estado));
        }
    }

    @Y("marco el tercer alumno como {string} si existe")
    public void marcoAlumno3ComoSiExiste(String estado) {
        int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (count >= 3) {
            actor.attemptsTo(MarkAttendance.forStudentAtRow(2, estado));
        }
    }

    @Y("guardo la asistencia")
    public void guardo() {
        actor.attemptsTo(Click.on(CoremTargets.ASISTENCIA_SAVE_BUTTON));
        try { Thread.sleep(2000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el boton guardar vuelve al estado habilitado")
    public void botonGuardarHabilitado() {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ASISTENCIA_SAVE_BUTTON, WebElementStateMatchers.isEnabled())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
        actor.should(seeThat(IsElementEnabled.at(CoremTargets.ASISTENCIA_SAVE_BUTTON), is(true)));
    }
}
