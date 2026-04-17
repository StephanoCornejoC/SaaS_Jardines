package com.corem.saas.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.annotations.Subject;
import net.serenitybdd.screenplay.targets.Target;

/**
 * Question: verifica si un elemento esta habilitado (no disabled).
 */
@Subject("el elemento '#target' esta habilitado")
public class IsElementEnabled implements Question<Boolean> {

    private final Target target;

    private IsElementEnabled(Target target) {
        this.target = target;
    }

    public static IsElementEnabled at(Target target) {
        return new IsElementEnabled(target);
    }

    @Override
    public Boolean answeredBy(Actor actor) {
        try {
            return target.resolveFor(actor).isEnabled();
        } catch (Exception e) {
            return false;
        }
    }
}
