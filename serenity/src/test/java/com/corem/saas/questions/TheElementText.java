package com.corem.saas.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.annotations.Subject;
import net.serenitybdd.screenplay.targets.Target;

/**
 * Question: Obtiene el texto de un elemento Target.
 *
 * Uso:
 *   actor.should(seeThat(TheElementText.of(CoremTargets.ANT_MODAL_TITLE), equalTo("Editar Alumno")));
 */
@Subject("el texto del elemento '#target'")
public class TheElementText implements Question<String> {

    private final Target target;

    private TheElementText(Target target) {
        this.target = target;
    }

    public static TheElementText of(Target target) {
        return new TheElementText(target);
    }

    @Override
    public String answeredBy(Actor actor) {
        try {
            return target.resolveFor(actor).getText().trim();
        } catch (Exception e) {
            return "";
        }
    }
}
