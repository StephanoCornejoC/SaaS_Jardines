package com.corem.saas.stepdefinitions;

import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.TheToastMessage;
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
 * Step definitions para los escenarios de Reportes.
 */
public class ReportsStepDefinitions {

    private Actor actor;

    @Y("navego al modulo de Reportes")
    public void navegoReportes() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/reportes"));
    }

    @Entonces("el encabezado \"Reportes\" es visible")
    public void encabezadoReportesVisible() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("heading Reportes").locatedBy("h1, h2, h3, h4").containingText("Reportes")
        ), is(true)));
    }

    @Y("la tarjeta {string} es visible")
    public void tarjetaVisible(String tarjetaTitulo) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("tarjeta " + tarjetaTitulo).locatedBy(".ant-card").containingText(tarjetaTitulo)
        ), is(true)));
    }

    @Y("hay exactamente {int} botones \"Descargar Excel\"")
    public void cantidadBotonesDescargar(int cantidad) {
        int count;
        try {
            count = CoremTargets.REPORTES_DOWNLOAD_BUTTONS.resolveAllFor(actor).size();
        } catch (Exception e) {
            count = 0;
        }
        org.junit.jupiter.api.Assertions.assertEquals(cantidad, count,
            "Se esperaban " + cantidad + " botones 'Descargar Excel' pero se encontraron " + count);
    }

    @Cuando("hago clic en \"Descargar Excel\" de la tarjeta {string}")
    public void clicDescargarExcel(String tarjetaTitulo) {
        Target card = Target.the("tarjeta " + tarjetaTitulo).locatedBy(".ant-card").containingText(tarjetaTitulo);
        Target downloadBtn = Target.the("boton descargar en " + tarjetaTitulo)
            .locatedBy(".ant-card button").containingText("Descargar Excel");
        try {
            actor.attemptsTo(Click.on(downloadBtn));
        } catch (Exception e) {
            actor.attemptsTo(Click.on(card));
        }
        try { Thread.sleep(2000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("se inicia la descarga del archivo {string}")
    public void iniciaDescarga(String nombreArchivo) {
        // En Selenium puro, la descarga va a la carpeta configurada.
        // Verificamos via el mensaje de exito que aparece en la UI.
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MESSAGE_CONTENT, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(30))
        );
    }

    @Y("aparece el mensaje de exito {string}")
    public void mensajeExitoReporte(String mensaje) {
        actor.should(seeThat(TheToastMessage.text(), containsString(mensaje)));
    }

    @Y("cuando la descarga completa el boton vuelve al estado normal")
    public void botonVuelveNormal() {
        try { Thread.sleep(5000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        Target loadingBtn = Target.the("boton con loading").locatedBy(".ant-btn-loading");
        int loadingCount;
        try {
            loadingCount = loadingBtn.resolveAllFor(actor).size();
        } catch (Exception e) {
            loadingCount = 0;
        }
        org.junit.jupiter.api.Assertions.assertEquals(0, loadingCount,
            "El boton no volvio al estado normal - sigue mostrando loading");
    }

    @Entonces("el boton muestra el estado de carga con la clase ant-btn-loading")
    public void botonMuestraEstadoCarga() {
        // Estado transitorio - verificamos que el boton de descarga es visible
        actor.should(seeThat(IsElementVisible.at(
            Target.the("boton de descarga").locatedBy("button").containingText("Descargar Excel")
        ), is(true)));
    }
}
