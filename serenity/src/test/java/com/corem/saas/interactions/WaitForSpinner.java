package com.corem.saas.interactions;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.waits.WaitUntil;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.annotations.Step;

import java.time.Duration;

/**
 * Interaccion que espera a que el spinner de Ant Design desaparezca.
 *
 * Muchas paginas de COREM hacen fetch al cargar y muestran un .ant-spin-spinning
 * hasta que los datos esten disponibles. Esta interaccion es esencial para
 * evitar flakiness por condiciones de carrera.
 */
public class WaitForSpinner implements Interaction {

    private final int timeoutSeconds;

    private WaitForSpinner(int timeoutSeconds) {
        this.timeoutSeconds = timeoutSeconds;
    }

    public static WaitForSpinner toDisappear() {
        return new WaitForSpinner(10);
    }

    public static WaitForSpinner toDisappearWithTimeout(int seconds) {
        return new WaitForSpinner(seconds);
    }

    @Override
    @Step("{0} espera a que el spinner de carga desaparezca")
    public <T extends Actor> void performAs(T actor) {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_SPINNER, WebElementStateMatchers.isNotVisible())
                .forNoMoreThan(Duration.ofSeconds(timeoutSeconds))
        );
    }
}
