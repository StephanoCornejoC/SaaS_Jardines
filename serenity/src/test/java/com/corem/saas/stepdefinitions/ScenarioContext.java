package com.corem.saas.stepdefinitions;

import com.corem.saas.abilities.CallTheCoremApi;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;
import net.thucydides.core.webdriver.ThucydidesWebDriverSupport;

/**
 * Contexto compartido entre todos los step definitions de un escenario.
 *
 * En Serenity 4.x, whoCan() acepta una ability a la vez.
 * Para multiples abilities, encadenar llamadas.
 */
public class ScenarioContext {

    private static final ThreadLocal<Actor> CURRENT_ACTOR = new ThreadLocal<>();

    private ScenarioContext() {}

    /**
     * Obtiene el actor del escenario actual, creandolo si no existe.
     */
    public static Actor getActor() {
        if (CURRENT_ACTOR.get() == null) {
            Actor actor = Actor.named("Administrador COREM");
            actor.whoCan(BrowseTheWeb.with(ThucydidesWebDriverSupport.getDriver()));
            actor.whoCan(CallTheCoremApi.forLocalEnvironment());
            CURRENT_ACTOR.set(actor);
        }
        return CURRENT_ACTOR.get();
    }

    /**
     * Limpia el actor al finalizar un escenario.
     */
    public static void reset() {
        CURRENT_ACTOR.remove();
    }
}
