package com.corem.saas.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.annotations.Subject;
import net.serenitybdd.screenplay.targets.Target;

/**
 * Question: verifica si un elemento es visible en la pagina.
 *
 * Uso correcto con seeThat():
 *   actor.should(seeThat(IsElementVisible.at(CoremTargets.LOGIN_BUTTON), is(true)));
 */
@Subject("el elemento '#target' es visible")
public class IsElementVisible implements Question<Boolean> {

    private final Target target;

    private IsElementVisible(Target target) {
        this.target = target;
    }

    public static IsElementVisible at(Target target) {
        return new IsElementVisible(target);
    }

    @Override
    public Boolean answeredBy(Actor actor) {
        try {
            return target.resolveFor(actor).isCurrentlyVisible();
        } catch (Exception e) {
            return false;
        }
    }
}
