package com.corem.saas.stepdefinitions;

import com.corem.saas.abilities.CallTheCoremApi;
import com.corem.saas.helpers.CoremApiClient;
import com.corem.saas.helpers.TestDataStore;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.ThePageUrl;
import com.corem.saas.questions.TheTableRowCount;
import com.corem.saas.questions.TheToastMessage;
import com.corem.saas.tasks.CreateStudent;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.After;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Clear;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Alumnos.
 * Feature: students/alumnos.feature
 */
public class StudentsStepDefinitions {

    private Actor actor;

    @After("@alumnos")
    public void cleanupStudents() {
        TestDataStore store = TestDataStore.getInstance();
        if (store.has(TestDataStore.ALUMNO_ID)) {
            try {
                CoremApiClient api = CallTheCoremApi.as(ScenarioContext.getActor());
                api.deleteStudent(store.get(TestDataStore.ALUMNO_ID));
            } catch (Exception ignored) {}
            store.remove(TestDataStore.ALUMNO_ID);
        }
    }

    @Y("navego al modulo de Alumnos")
    public void navegoAlumnos() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/alumnos"));
    }

    @Entonces("el encabezado \"Alumnos\" es visible")
    public void encabezadoAlumnosVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ALUMNOS_HEADING), is(true)));
    }

    @Y("la tabla de alumnos esta presente")
    public void tablaAlumnosPresente() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ALUMNOS_TABLE), is(true)));
    }

    @Y("la tabla contiene las columnas {string}, {string}, {string}, {string}, {string}")
    public void tablaContieneColumnas(String col1, String col2, String col3, String col4, String col5) {
        for (String col : new String[]{col1, col2, col3, col4, col5}) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("columna " + col).locatedBy(".ant-table-thead th").containingText(col)
            ), is(true)));
        }
    }

    @Y("el boton {string} esta disponible")
    public void botonDisponible(String botonTexto) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("boton " + botonTexto).locatedBy("button").containingText(botonTexto)
        ), is(true)));
    }

    @Cuando("abro el modal de creacion de alumno")
    public void abroModalCreacion() {
        actor.attemptsTo(Click.on(CoremTargets.ALUMNOS_NEW_BUTTON));
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
    }

    @Y("lleno el formulario con los datos del alumno:")
    public void llenoFormularioAlumno(DataTable datosTable) {
        List<Map<String, String>> rows = datosTable.asMaps(String.class, String.class);
        Map<String, String> datos = new HashMap<>();
        for (Map<String, String> row : rows) {
            datos.put(row.get("campo"), row.get("valor"));
        }
        actor.attemptsTo(
            CreateStudent.withData(
                datos.get("DNI"),
                datos.get("Nombres"),
                datos.get("Apellidos"),
                datos.get("Fecha Nacimiento"),
                datos.get("Genero")
            )
        );
    }

    @Y("guardo el formulario")
    public void guardo() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    @Entonces("aparece el mensaje de exito {string}")
    public void mensajeExito(String mensaje) {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MESSAGE_CONTENT, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(8))
        );
        actor.should(seeThat(TheToastMessage.text(), containsString(mensaje)));
    }

    @Y("el alumno con DNI {string} aparece en la tabla")
    public void alumnoEnTabla(String dni) {
        actor.attemptsTo(Enter.theValue(dni).into(CoremTargets.ALUMNOS_SEARCH_INPUT));
        try { Thread.sleep(800); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        actor.should(seeThat(TheTableRowCount.inTheCurrentTable(), greaterThanOrEqualTo(1)));
    }

    @Cuando("intento guardar el formulario sin llenar ningun campo")
    public void intentoGuardarSinCampos() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    @Entonces("el modal muestra el error {string} en el campo {string}")
    public void modalMuestraError(String error, String campo) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("error en campo " + campo).locatedBy(".ant-modal .ant-form-item-explain-error")
        ), is(true)));
    }

    @Y("el modal de alumno permanece abierto")
    public void modalAlumnoPermanece() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_MODAL), is(true)));
    }

    @Dado("existe un alumno con DNI {string} y nombre {string} creado via API")
    public void alumnoExisteViaApi(String dni, String nombres) {
        actor = ScenarioContext.getActor();
        CoremApiClient api = CallTheCoremApi.as(actor);
        String[] partes = nombres.split(" ");
        String apellidos = partes.length > 1 ? partes[1] : "Test";
        String primerNombre = partes[0];
        Map<String, Object> student = api.createStudent(dni, primerNombre, apellidos, "2019-06-20", "F");
        TestDataStore.getInstance().put(TestDataStore.ALUMNO_ID, student.get("id"));
        TestDataStore.getInstance().put(TestDataStore.ALUMNO_DNI, dni);
    }

    @Dado("existe un alumno con nombre unico {string} creado via API")
    public void alumnoConNombreUnico(String nombreUnico) {
        actor = ScenarioContext.getActor();
        CoremApiClient api = CallTheCoremApi.as(actor);
        String dniUnico = "9" + (System.currentTimeMillis() % 10000000);
        Map<String, Object> student = api.createStudent(dniUnico, nombreUnico, "Prueba", "2021-03-10", "M");
        TestDataStore.getInstance().put(TestDataStore.ALUMNO_ID, student.get("id"));
        TestDataStore.getInstance().put(TestDataStore.ALUMNO_DNI, dniUnico);
        TestDataStore.getInstance().put(TestDataStore.ALUMNO_NOMBRES, nombreUnico);
    }

    @Cuando("busco el alumno por DNI {string}")
    public void buscoAlumnoPorDni(String dni) {
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNOS_SEARCH_INPUT),
            Enter.theValue(dni).into(CoremTargets.ALUMNOS_SEARCH_INPUT)
        );
        try { Thread.sleep(800); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Cuando("busco el alumno por nombre {string}")
    public void buscoAlumnoPorNombre(String nombre) {
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNOS_SEARCH_INPUT),
            Enter.theValue(nombre).into(CoremTargets.ALUMNOS_SEARCH_INPUT)
        );
        try { Thread.sleep(800); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Cuando("abro el modal de edicion del primer resultado")
    public void abroModalEdicion() {
        Target editButton = Target.the("boton de edicion").locatedBy(
            ".ant-table-tbody tr.ant-table-row:first-child .anticon-edit, " +
            ".ant-table-tbody tr.ant-table-row:first-child button[title*='Editar']"
        );
        actor.attemptsTo(Click.on(editButton));
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
    }

    @Entonces("el titulo del modal es {string}")
    public void tituloModal(String titulo) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("modal con titulo " + titulo).locatedBy(".ant-modal").containingText(titulo)
        ), is(true)));
    }

    @Cuando("modifico el nombre a {string}")
    public void modificoNombre(String nuevoNombre) {
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNO_FORM_NOMBRES),
            Clear.field(CoremTargets.ALUMNO_FORM_NOMBRES),
            Enter.theValue(nuevoNombre).into(CoremTargets.ALUMNO_FORM_NOMBRES)
        );
    }

    @Entonces("el nombre {string} aparece en la tabla para el DNI {string}")
    public void nombreEnTablaParaDni(String nombre, String dni) {
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNOS_SEARCH_INPUT),
            Enter.theValue(dni).into(CoremTargets.ALUMNOS_SEARCH_INPUT)
        );
        try { Thread.sleep(800); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        actor.should(seeThat(IsElementVisible.at(
            Target.the("nombre en tabla").locatedBy(".ant-table-tbody td").containingText(nombre)
        ), is(true)));
    }

    @Entonces("la tabla muestra exactamente {int} resultado")
    public void tablaMuestraResultados(int count) {
        actor.should(seeThat(TheTableRowCount.inTheCurrentTable(), equalTo(count)));
    }

    @Y("el nombre {string} aparece en la primera fila de la tabla")
    public void nombrePrimeraFila(String nombre) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("nombre en primera fila")
                .locatedBy(".ant-table-tbody tr.ant-table-row:first-child td")
                .containingText(nombre)
        ), is(true)));
    }

    @Cuando("hago clic en el icono de ver del primer resultado")
    public void clicIconoVer() {
        Target viewButton = Target.the("boton de ver").locatedBy(
            ".ant-table-tbody tr.ant-table-row:first-child .anticon-eye, " +
            ".ant-table-tbody tr.ant-table-row:first-child button[title*='Ver']"
        );
        actor.attemptsTo(Click.on(viewButton));
    }

    @Entonces("la URL contiene {string}")
    public void urlContiene(String fragment) {
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString(fragment)));
    }

    @Y("la pagina de detalle muestra el nombre {string}")
    public void paginaDetalleNombre(String nombre) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("nombre en detalle").locatedBy("h1, h2, h3, h4").containingText(nombre)
        ), is(true)));
    }
}
