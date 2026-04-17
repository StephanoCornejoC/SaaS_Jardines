package com.corem.saas.tasks;

import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.interactions.TypeInAntdPicker;
import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.annotations.Step;

/**
 * Task: Crear una nueva transaccion de Flujo de Caja.
 *
 * Prerrequisito: el modal de nueva transaccion debe estar abierto.
 */
public class CreateTransaction implements Task {

    private final String tipo;
    private final String categoria;
    private final String descripcion;
    private final double monto;
    private final String fecha;

    private CreateTransaction(String tipo, String categoria, String descripcion,
                               double monto, String fecha) {
        this.tipo = tipo;
        this.categoria = categoria;
        this.descripcion = descripcion;
        this.monto = monto;
        this.fecha = fecha;
    }

    public static Builder ofType(String tipo) {
        return new Builder(tipo);
    }

    @Override
    @Step("{0} crea una transaccion de tipo '#tipo' por S/ #monto")
    public <T extends Actor> void performAs(T actor) {
        // Tipo de transaccion
        Target tipoSelect = Target.the("select de tipo de transaccion")
            .locatedBy(".ant-modal .ant-form-item:nth-of-type(1) .ant-select");
        actor.attemptsTo(
            Click.on(tipoSelect),
            SelectFromAntdDropdown.withOption(tipo).from(tipoSelect)
        );

        // Categoria
        Target categoriaSelect = Target.the("select de categoria")
            .locatedBy(".ant-modal .ant-form-item:nth-of-type(2) .ant-select");
        actor.attemptsTo(
            Click.on(categoriaSelect),
            SelectFromAntdDropdown.withOption(categoria).from(categoriaSelect)
        );

        // Descripcion
        Target descripcionInput = Target.the("campo de descripcion")
            .locatedBy(".ant-modal input[placeholder*='descripcion'], .ant-modal input[placeholder*='Descripcion'], .ant-modal #transaccionForm_descripcion");
        actor.attemptsTo(Enter.theValue(descripcion).into(descripcionInput));

        // Monto
        Target montoInput = Target.the("campo de monto")
            .locatedBy(".ant-modal .ant-input-number-input, .ant-modal input[type='number']");
        actor.attemptsTo(Enter.theValue(String.valueOf(monto)).into(montoInput));

        // Fecha (DatePicker)
        actor.attemptsTo(
            TypeInAntdPicker.withValue(fecha)
                .in(Target.the("datepicker de fecha").locatedBy(".ant-modal .ant-picker input"))
        );

        // Guardar
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    public static class Builder {
        private String tipo;
        private String categoria = "Otros";
        private String descripcion = "Transaccion de test";
        private double monto = 100.0;
        private String fecha = "01/01/2026";

        Builder(String tipo) {
            this.tipo = tipo;
        }

        public Builder withCategory(String categoria) {
            this.categoria = categoria;
            return this;
        }

        public Builder withDescription(String descripcion) {
            this.descripcion = descripcion;
            return this;
        }

        public Builder withAmount(double monto) {
            this.monto = monto;
            return this;
        }

        public Builder onDate(String fecha) {
            this.fecha = fecha;
            return this;
        }

        public CreateTransaction build() {
            return new CreateTransaction(tipo, categoria, descripcion, monto, fecha);
        }
    }
}
