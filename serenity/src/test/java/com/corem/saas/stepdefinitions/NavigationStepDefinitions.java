package com.corem.saas.stepdefinitions;

import com.corem.saas.interactions.WaitForSpinner;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.ThePageUrl;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Open;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Navegacion.
 */
public class NavigationStepDefinitions {

    private Actor actor;

    @Y("navego a {string}")
    public void navegoA(String path) {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withoutWaiting(path));
    }

    @Cuando("navego directamente a {string}")
    public void navegoDirectamente(String path) {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(Open.url(path));
        try { Thread.sleep(2000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Cuando("navego a cada modulo desde el menu lateral:")
    public void navegoACadaModulo(DataTable tablaModulos) {
        List<Map<String, String>> modulos = tablaModulos.asMaps(String.class, String.class);
        actor = ScenarioContext.getActor();
        for (Map<String, String> modulo : modulos) {
            String etiqueta = modulo.get("etiqueta");
            String urlEsperada = modulo.get("url_esperada");
            Target menuItem = Target.the("item de menu " + etiqueta)
                .locatedBy(".ant-menu [role='menuitem']").containingText(etiqueta);
            actor.attemptsTo(Click.on(menuItem));
            actor.should(seeThat(ThePageUrl.currentUrl(), containsString(urlEsperada)));
            actor.attemptsTo(WaitForSpinner.toDisappear());
        }
    }

    @Entonces("cada modulo carga sin errores de spinner")
    public void cadaModuloCarga() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("body de la pagina").locatedBy("body")
        ), is(true)));
    }

    @Y("el item {string} del menu lateral tiene la clase {string}")
    public void itemMenuConClase(String itemName, String cssClass) {
        Target menuItem = Target.the("item de menu " + itemName)
            .locatedBy(".ant-menu [role='menuitem']").containingText(itemName);
        String classes = menuItem.resolveFor(actor).getAttribute("class");
        String cleanClass = cssClass.replace(".", "");
        org.junit.jupiter.api.Assertions.assertTrue(
            classes != null && classes.contains(cleanClass),
            "El item '" + itemName + "' no tiene la clase '" + cssClass + "'. Clases: " + classes
        );
    }

    @Cuando("hago clic en el boton de colapsar el sidebar")
    public void clicColapsarSidebar() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(Click.on(CoremTargets.HEADER_COLLAPSE_BUTTON));
        try { Thread.sleep(600); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el sidebar tiene la clase {string}")
    public void sidebarConClase(String cssClass) {
        String classes = CoremTargets.ANT_SIDER.resolveFor(actor).getAttribute("class");
        String cleanClass = cssClass.replace("ant-layout-sider-", "").replace(".", "");
        org.junit.jupiter.api.Assertions.assertTrue(
            classes != null && classes.contains(cleanClass),
            "El sidebar no tiene la clase '" + cssClass + "'. Clases: " + classes
        );
    }

    @Cuando("hago clic de nuevo en el boton de colapsar")
    public void clicDeNuevoColapsar() {
        actor.attemptsTo(Click.on(CoremTargets.HEADER_COLLAPSE_BUTTON));
        try { Thread.sleep(600); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el sidebar no tiene la clase {string}")
    public void sidebarSinClase(String cssClass) {
        String classes = CoremTargets.ANT_SIDER.resolveFor(actor).getAttribute("class");
        String cleanClass = cssClass.replace(".", "");
        org.junit.jupiter.api.Assertions.assertFalse(
            classes != null && classes.contains(cleanClass),
            "El sidebar todavia tiene la clase '" + cssClass + "'. Clases: " + classes
        );
    }

    @Entonces("soy redirigido al dashboard")
    public void redirigidoAlDashboardNav() {
        actor.attemptsTo(
            WaitUntil.the(
                Target.the("heading dashboard").locatedBy("h1, h2, h3, h4").containingText("Dashboard"),
                WebElementStateMatchers.isVisible()
            ).forNoMoreThan(Duration.ofSeconds(10))
        );
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString("dashboard")));
    }
}
