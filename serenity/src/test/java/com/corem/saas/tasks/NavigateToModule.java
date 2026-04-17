package com.corem.saas.tasks;

import com.corem.saas.interactions.WaitForSpinner;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Open;
import net.serenitybdd.annotations.Step;

/**
 * Task: Navegar a un modulo de SAAS COREM via URL directa.
 *
 * Uso:
 *   actor.attemptsTo(NavigateToModule.named("alumnos"));
 *   actor.attemptsTo(NavigateToModule.withPath("/dashboard"));
 */
public class NavigateToModule implements Task {

    private final String path;
    private final boolean waitForLoad;

    private NavigateToModule(String path, boolean waitForLoad) {
        this.path = path;
        this.waitForLoad = waitForLoad;
    }

    public static NavigateToModule withPath(String path) {
        return new NavigateToModule(path, true);
    }

    public static NavigateToModule named(String moduleName) {
        return new NavigateToModule("/" + moduleName, true);
    }

    public static NavigateToModule withoutWaiting(String path) {
        return new NavigateToModule(path, false);
    }

    @Override
    @Step("{0} navega al modulo '#path'")
    public <T extends Actor> void performAs(T actor) {
        actor.attemptsTo(Open.url(path));
        if (waitForLoad) {
            actor.attemptsTo(WaitForSpinner.toDisappear());
        }
    }
}
