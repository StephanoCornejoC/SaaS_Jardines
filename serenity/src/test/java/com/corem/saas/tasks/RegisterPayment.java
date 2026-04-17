package com.corem.saas.tasks;

import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.annotations.Step;

/**
 * Task: Registrar un pago en el modal de Pensiones.
 *
 * Prerrequisito: el modal de pago debe estar abierto.
 */
public class RegisterPayment implements Task {

    private final String metodoPago;
    private final String observaciones;

    private RegisterPayment(String metodoPago, String observaciones) {
        this.metodoPago = metodoPago;
        this.observaciones = observaciones;
    }

    public static RegisterPayment withMethod(String metodoPago) {
        return new RegisterPayment(metodoPago, "");
    }

    public RegisterPayment andObservations(String observaciones) {
        return new RegisterPayment(this.metodoPago, observaciones);
    }

    public static RegisterPayment withMethodAndObservations(String metodoPago, String observaciones) {
        return new RegisterPayment(metodoPago, observaciones);
    }

    @Override
    @Step("{0} registra el pago con metodo '#metodoPago'")
    public <T extends Actor> void performAs(T actor) {
        // Seleccionar metodo de pago
        Target metodoPagoSelect = Target.the("select de metodo de pago")
            .locatedBy(".ant-modal .ant-select");
        actor.attemptsTo(
            Click.on(metodoPagoSelect),
            SelectFromAntdDropdown.withOption(metodoPago).from(metodoPagoSelect)
        );

        // Agregar observaciones si existen
        if (observaciones != null && !observaciones.isEmpty()) {
            Target obsInput = Target.the("campo de observaciones")
                .locatedBy(".ant-modal textarea, .ant-modal input[placeholder*='observa']");
            actor.attemptsTo(Enter.theValue(observaciones).into(obsInput));
        }

        // Confirmar el pago
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }
}
