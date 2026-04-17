package com.corem.saas.actors;

import com.corem.saas.abilities.CallTheCoremApi;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;
import net.thucydides.core.webdriver.ThucydidesWebDriverSupport;

/**
 * Factory de actores para los tests de SAAS COREM.
 *
 * Centraliza la creacion de actores con las abilities necesarias
 * segun el tipo de test (solo UI, UI + API, solo API).
 *
 * Nota: en Serenity 4.x, whoCan() acepta una ability a la vez.
 * Para multiples abilities, se encadenan llamadas.
 */
public class CoremActors {

    private CoremActors() {}

    /**
     * Crea un actor administrador con capacidad de navegar la web y llamar la API.
     */
    public static Actor admin() {
        Actor admin = Actor.named("Administrador");
        admin.whoCan(BrowseTheWeb.with(ThucydidesWebDriverSupport.getDriver()));
        admin.whoCan(CallTheCoremApi.forLocalEnvironment());
        return admin;
    }

    /**
     * Crea un actor anonimo (sin sesion) para tests de control de acceso.
     */
    public static Actor anonymous() {
        Actor anonymous = Actor.named("Usuario Anonimo");
        anonymous.whoCan(BrowseTheWeb.with(ThucydidesWebDriverSupport.getDriver()));
        return anonymous;
    }

    /**
     * Crea un actor con nombre custom y capacidades de UI y API.
     */
    public static Actor withName(String name) {
        Actor actor = Actor.named(name);
        actor.whoCan(BrowseTheWeb.with(ThucydidesWebDriverSupport.getDriver()));
        actor.whoCan(CallTheCoremApi.forLocalEnvironment());
        return actor;
    }
}
