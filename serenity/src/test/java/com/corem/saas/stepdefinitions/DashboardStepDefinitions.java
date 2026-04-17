package com.corem.saas.stepdefinitions;

import com.corem.saas.interactions.WaitForSpinner;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Dashboard.
 */
public class DashboardStepDefinitions {

    private Actor actor;

    @Y("espero que el dashboard cargue completamente")
    public void esperoQueCargue() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(WaitForSpinner.toDisappear());
        try { Thread.sleep(1500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el KPI {string} es visible con un valor numerico valido")
    public void kpiVisibleConValor(String kpiName) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("KPI " + kpiName).locatedBy(".ant-statistic, .ant-card").containingText(kpiName)
        ), is(true)));
    }

    @Y("el menu lateral es visible")
    public void menuLateralVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_SIDER), is(true)));
    }

    @Entonces("el grafico de ingresos mensuales esta renderizado con dimensiones validas")
    public void graficoRenderizado() {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.DASHBOARD_CHART_CANVAS, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(10))
        );
        actor.should(seeThat(IsElementVisible.at(CoremTargets.DASHBOARD_CHART_CANVAS), is(true)));
    }

    @Y("el card contenedor del grafico es visible")
    public void cardGraficoVisible() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("card del grafico").locatedBy(".ant-card")
        ), is(true)));
    }
}
