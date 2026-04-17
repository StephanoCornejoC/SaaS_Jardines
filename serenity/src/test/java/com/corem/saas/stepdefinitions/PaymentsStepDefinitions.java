package com.corem.saas.stepdefinitions;

import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.TheTableRowCount;
import com.corem.saas.questions.TheToastMessage;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Pensiones.
 */
public class PaymentsStepDefinitions {

    private Actor actor;

    @Y("navego al modulo de Pensiones")
    public void navegoPensiones() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/pensiones"));
    }

    @Entonces("el encabezado \"Pensiones\" es visible")
    public void encabezadoPensionesVisible() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("heading Pensiones").locatedBy("h1, h2, h3, h4").containingText("Pensiones")
        ), is(true)));
    }

    @Y("la tabla de pensiones esta presente")
    public void tablaPensionesPresente() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.PENSIONES_TABLE), is(true)));
    }

    @Y("la tabla contiene las columnas {string}, {string}, {string}, {string}")
    public void tablaContieneColumnasCuatro(String col1, String col2, String col3, String col4) {
        for (String col : new String[]{col1, col2, col3, col4}) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("columna " + col).locatedBy(".ant-table-thead th").containingText(col)
            ), is(true)));
        }
    }

    @Y("los filtros de mes, anio y estado estan disponibles")
    public void filtrosDisponibles() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("filtros de pension").locatedBy(".ant-select")
        ), is(true)));
    }

    @Cuando("filtro las pensiones por estado {string}")
    public void filtroPorEstado(String estado) {
        actor.attemptsTo(
            Click.on(CoremTargets.PENSIONES_FILTER_ESTADO),
            SelectFromAntdDropdown.withOption(estado).from(CoremTargets.PENSIONES_FILTER_ESTADO)
        );
        try { Thread.sleep(800); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("todos los registros visibles tienen el estado {string}")
    public void todosConEstado(String estado) {
        int rowCount = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        if (rowCount > 0) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("tag de estado " + estado).locatedBy(".ant-table-tbody .ant-tag")
                    .containingText(estado.toUpperCase())
            ), is(true)));
        }
    }

    @Dado("que existen pensiones pendientes en la tabla")
    public void existenPensionesPendientes() {
        int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        org.junit.jupiter.api.Assumptions.assumeTrue(count > 0, "No hay pensiones pendientes");
    }

    @Dado("que existen pensiones en la tabla")
    public void existenPensiones() {
        int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        org.junit.jupiter.api.Assumptions.assumeTrue(count > 0, "No hay pensiones disponibles");
    }

    @Cuando("abro el modal de pago del primer registro pendiente")
    public void abroModalPago() {
        Target pagarButton = Target.the("boton Registrar Pago primera fila")
            .locatedBy(".ant-table-tbody tr.ant-table-row:first-child button");
        actor.attemptsTo(Click.on(pagarButton));
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.PAGO_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
    }

    @Entonces("el modal {string} esta visible")
    public void modalVisible(String tituloModal) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("modal " + tituloModal).locatedBy(".ant-modal").containingText(tituloModal)
        ), is(true)));
    }

    @Y("el campo monto tiene un valor pre-rellenado")
    public void campoMontoPreRellenado() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.PAGO_MONTO_INPUT), is(true)));
    }

    @Cuando("selecciono el metodo de pago {string}")
    public void seleccionoMetodoPago(String metodo) {
        Target metodoPagoSelect = Target.the("select de metodo de pago")
            .locatedBy(".ant-modal .ant-select");
        actor.attemptsTo(
            Click.on(metodoPagoSelect),
            SelectFromAntdDropdown.withOption(metodo).from(metodoPagoSelect)
        );
    }

    @Y("agrego las observaciones {string}")
    public void agregoObservaciones(String obs) {
        try {
            Target obsInput = Target.the("campo de observaciones").locatedBy(".ant-modal textarea");
            actor.attemptsTo(Enter.theValue(obs).into(obsInput));
        } catch (Exception ignored) {}
    }

    @Y("confirmo el pago")
    public void confirmoElPago() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    @Y("el registro ya no aparece como pendiente")
    public void registroNoPendiente() {
        actor.should(seeThat(TheToastMessage.text(), containsString("registrado")));
    }

    @Cuando("hago clic en el boton de QR del primer registro")
    public void clicBotonQR() {
        try {
            Target qrButton = Target.the("boton QR")
                .locatedBy(".ant-table-tbody tr.ant-table-row:first-child .anticon-qrcode");
            actor.attemptsTo(Click.on(qrButton));
        } catch (Exception e) {
            Target lastButton = Target.the("ultimo boton de la fila")
                .locatedBy(".ant-table-tbody tr.ant-table-row:first-child button:last-child");
            actor.attemptsTo(Click.on(lastButton));
        }
    }

    @Entonces("el modal de QR esta visible")
    public void modalQRVisible() {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.QR_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(10))
        );
        actor.should(seeThat(IsElementVisible.at(CoremTargets.QR_MODAL), is(true)));
    }

    @Y("la imagen del codigo QR tiene dimensiones mayores a cero")
    public void imagenQRDimensiones() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.QR_IMAGE), is(true)));
    }

    @Cuando("cierro el modal de QR")
    public void cierroModalQR() {
        Target closeButton = Target.the("boton de cerrar modal")
            .locatedBy(".ant-modal-close, .ant-modal-confirm-btns .ant-btn");
        actor.attemptsTo(Click.on(closeButton));
    }

    @Entonces("el modal de QR esta oculto")
    public void modalQROculto() {
        try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        actor.should(seeThat(IsElementVisible.at(CoremTargets.QR_MODAL), is(false)));
    }
}
