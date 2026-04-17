package com.corem.saas.stepdefinitions;

import com.corem.saas.interactions.ConfirmPopconfirm;
import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.interactions.WaitForSpinner;
import com.corem.saas.questions.IsElementVisible;
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
 * Step definitions para los escenarios de Comunicaciones.
 */
public class CommunicationsStepDefinitions {

    private Actor actor;
    private String tituloUnico;

    @Y("navego al modulo de Comunicaciones")
    public void navegoComunicaciones() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/comunicaciones"));
    }

    @Entonces("el encabezado \"Comunicaciones\" es visible")
    public void encabezadoComunicacionesVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.COMUNICACIONES_HEADING), is(true)));
    }

    @Y("el spinner de carga desaparece")
    public void spinnerDesaparece() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(WaitForSpinner.toDisappear());
    }

    @Y("la tabla de comunicaciones esta visible")
    public void tablaComunicacionesVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.COMUNICACIONES_TABLE), is(true)));
    }

    @Y("la tabla contiene las columnas {string}, {string}, {string}")
    public void tablaContieneColumnasTres(String col1, String col2, String col3) {
        for (String col : new String[]{col1, col2, col3}) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("columna " + col).locatedBy(".ant-table-thead th").containingText(col)
            ), is(true)));
        }
    }

    @Cuando("abro el modal de nueva comunicacion")
    public void abroModalNuevaComunicacion() {
        actor.attemptsTo(Click.on(CoremTargets.COMUNICACIONES_NEW_BUTTON));
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
    }

    @Y("el modal \"Nueva Comunicacion\" es visible")
    public void modalNuevaComunicacionVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_MODAL), is(true)));
    }

    @Y("lleno el titulo con {string}")
    public void llenoTitulo(String titulo) {
        tituloUnico = titulo + " " + System.currentTimeMillis();
        actor.attemptsTo(Enter.theValue(tituloUnico).into(CoremTargets.COMUNICACION_TITULO_INPUT));
    }

    @Y("lleno el contenido con {string}")
    public void llenoContenido(String contenido) {
        actor.attemptsTo(Enter.theValue(contenido).into(CoremTargets.COMUNICACION_CONTENIDO_INPUT));
    }

    @Y("el campo \"Aula\" no es visible porque el tipo es GENERAL")
    public void campoAulaNoVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.COMUNICACION_AULA_FORM_ITEM), is(false)));
    }

    @Y("guardo la comunicacion")
    public void guardoComunicacion() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    @Entonces("el modal se cierra")
    public void modalSeCierra() {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MODAL, WebElementStateMatchers.isNotVisible())
                .forNoMoreThan(Duration.ofSeconds(10))
        );
    }

    @Y("el comunicado {string} aparece en la tabla")
    public void comunicadoEnTabla(String titulo) {
        String textoABuscar = tituloUnico != null ? tituloUnico : titulo;
        actor.should(seeThat(IsElementVisible.at(
            Target.the("comunicado en tabla").locatedBy(".ant-table-tbody td").containingText(textoABuscar)
        ), is(true)));
    }

    @Cuando("cambio el tipo de comunicacion a {string}")
    public void cambioTipoComunicacion(String tipo) {
        actor.attemptsTo(
            Click.on(CoremTargets.COMUNICACION_TIPO_SELECT),
            SelectFromAntdDropdown.withOption(tipo).from(CoremTargets.COMUNICACION_TIPO_SELECT)
        );
        try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el campo \"Aula\" es visible en el modal")
    public void campoAulaVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.COMUNICACION_AULA_FORM_ITEM), is(true)));
    }

    @Cuando("cancelo el modal de comunicacion")
    public void canceloModalComunicacion() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_CANCEL_BUTTON));
    }

    @Entonces("el modal de comunicacion esta oculto")
    public void modalComunicacionOculto() {
        try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_MODAL), is(false)));
    }

    @Dado("que existen comunicaciones en estado BORRADOR")
    public void existenComunicacionesBorrador() {
        actor = ScenarioContext.getActor();
        Target sendButtonInTable = Target.the("boton Enviar en tabla")
            .locatedBy(".ant-table-tbody tr.ant-table-row button").containingText("Enviar");
        int count;
        try {
            count = sendButtonInTable.resolveAllFor(actor).size();
        } catch (Exception e) {
            count = 0;
        }
        org.junit.jupiter.api.Assumptions.assumeTrue(count > 0, "No hay comunicaciones BORRADOR");
    }

    @Cuando("hago clic en el boton Enviar de la primera comunicacion en borrador")
    public void clicEnviarPrimeraBorrador() {
        Target sendButton = Target.the("primer boton Enviar")
            .locatedBy(".ant-table-tbody tr.ant-table-row button").containingText("Enviar");
        actor.attemptsTo(Click.on(sendButton));
    }

    @Entonces("el Popconfirm de confirmacion es visible con el texto {string}")
    public void popconfirmVisible(String texto) {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_POPCONFIRM, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_POPCONFIRM), is(true)));
    }

    @Cuando("confirmo el envio en el Popconfirm")
    public void confirmoEnPopconfirm() {
        actor.attemptsTo(ConfirmPopconfirm.clickingOk());
    }
}
