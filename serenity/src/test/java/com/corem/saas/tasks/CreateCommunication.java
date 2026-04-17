package com.corem.saas.tasks;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.annotations.Step;

/**
 * Task: Crear una nueva comunicacion en el modulo de Comunicaciones.
 *
 * Prerrequisito: el modal de nueva comunicacion debe estar abierto.
 */
public class CreateCommunication implements Task {

    private final String titulo;
    private final String contenido;

    private CreateCommunication(String titulo, String contenido) {
        this.titulo = titulo;
        this.contenido = contenido;
    }

    public static CreateCommunication withTitle(String titulo) {
        return new CreateCommunication(titulo, "Contenido de prueba");
    }

    public CreateCommunication andContent(String contenido) {
        return new CreateCommunication(this.titulo, contenido);
    }

    @Override
    @Step("{0} crea la comunicacion con titulo '#titulo'")
    public <T extends Actor> void performAs(T actor) {
        actor.attemptsTo(
            Enter.theValue(titulo).into(CoremTargets.COMUNICACION_TITULO_INPUT),
            Enter.theValue(contenido).into(CoremTargets.COMUNICACION_CONTENIDO_INPUT),
            Click.on(CoremTargets.ANT_MODAL_OK_BUTTON)
        );
    }
}
