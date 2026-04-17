package com.corem.saas.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;
import net.serenitybdd.screenplay.annotations.Subject;

/**
 * Question: Devuelve la URL actual del browser.
 *
 * Uso:
 *   actor.should(seeThat(ThePageUrl.currentUrl(), containsString("/dashboard")));
 */
@Subject("la URL actual de la pagina")
public class ThePageUrl implements Question<String> {

    private ThePageUrl() {}

    public static ThePageUrl currentUrl() {
        return new ThePageUrl();
    }

    @Override
    public String answeredBy(Actor actor) {
        return BrowseTheWeb.as(actor).getDriver().getCurrentUrl();
    }
}
