package com.corem.saas.interactions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.annotations.Step;
import org.openqa.selenium.Keys;

/**
 * Interaccion para escribir una fecha en el DatePicker de Ant Design.
 *
 * El DatePicker de Ant Design requiere:
 * 1. Click en el input para abrirlo
 * 2. Escribir la fecha en formato DD/MM/YYYY
 * 3. Presionar Enter para confirmar
 */
public class TypeInAntdPicker implements Interaction {

    private final Target pickerTarget;
    private final String dateValue;

    private TypeInAntdPicker(Target pickerTarget, String dateValue) {
        this.pickerTarget = pickerTarget;
        this.dateValue = dateValue;
    }

    public static TypeInAntdPicker withValue(String date) {
        return new TypeInAntdPicker(null, date);
    }

    public TypeInAntdPicker in(Target target) {
        return new TypeInAntdPicker(target, dateValue);
    }

    @Override
    @Step("{0} escribe la fecha '#dateValue' en el DatePicker de Ant Design")
    public <T extends Actor> void performAs(T actor) {
        if (pickerTarget != null) {
            actor.attemptsTo(Click.on(pickerTarget));
            try {
                Thread.sleep(200);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        Target inputInPicker = pickerTarget != null
            ? Target.the("input del DatePicker").locatedBy(".ant-picker-focused input, .ant-picker-panel-container input")
            : Target.the("input del DatePicker").locatedBy(".ant-picker-focused input");

        actor.attemptsTo(
            Enter.theValue(dateValue).into(inputInPicker),
            Enter.theValue(Keys.ENTER.toString()).into(inputInPicker)
        );
    }
}
