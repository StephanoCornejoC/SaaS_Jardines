package com.corem.saas.interactions;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.annotations.Step;

/**
 * Interaccion para confirmar un Popconfirm de Ant Design.
 *
 * Un Popconfirm de Ant Design muestra un tooltip con botones Aceptar/Cancelar
 * cuando el usuario hace click en un boton con peligro potencial.
 * Esta interaccion hace click en el boton de confirmacion (OK/Aceptar).
 */
public class ConfirmPopconfirm implements Interaction {

    private ConfirmPopconfirm() {}

    public static ConfirmPopconfirm clickingOk() {
        return new ConfirmPopconfirm();
    }

    @Override
    @Step("{0} confirma el Popconfirm haciendo clic en OK")
    public <T extends Actor> void performAs(T actor) {
        actor.attemptsTo(Click.on(CoremTargets.ANT_POPCONFIRM_OK));
    }
}
