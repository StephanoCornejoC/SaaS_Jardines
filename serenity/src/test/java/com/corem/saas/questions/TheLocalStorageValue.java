package com.corem.saas.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;
import net.serenitybdd.screenplay.annotations.Subject;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;

/**
 * Question: Lee un valor del localStorage del browser.
 *
 * Util para verificar que el token JWT fue eliminado despues del logout.
 *
 * Uso:
 *   actor.should(seeThat(TheLocalStorageValue.forKey("access_token"), is(nullValue())));
 */
@Subject("el valor '#key' en localStorage")
public class TheLocalStorageValue implements Question<String> {

    private final String key;

    private TheLocalStorageValue(String key) {
        this.key = key;
    }

    public static TheLocalStorageValue forKey(String key) {
        return new TheLocalStorageValue(key);
    }

    @Override
    public String answeredBy(Actor actor) {
        try {
            WebDriver driver = BrowseTheWeb.as(actor).getDriver();
            if (driver instanceof JavascriptExecutor) {
                Object result = ((JavascriptExecutor) driver)
                    .executeScript("return localStorage.getItem('" + key + "');");
                return result != null ? result.toString() : null;
            }
            return null;
        } catch (Exception e) {
            return null;
        }
    }
}
