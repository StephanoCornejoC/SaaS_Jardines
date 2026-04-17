package com.corem.saas.interactions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.annotations.Step;

/**
 * Interaccion para seleccionar una opcion en un dropdown de Ant Design (ant-select).
 *
 * Los Select de Ant Design NO son select HTML nativos, sino divs custom
 * que abren un dropdown separado (.ant-select-dropdown). Esta interaccion
 * maneja ese comportamiento:
 * 1. Hace click en el select para abrir el dropdown
 * 2. Espera que el dropdown sea visible
 * 3. Hace click en la opcion deseada (por titulo o texto)
 */
public class SelectFromAntdDropdown implements Interaction {

    private final Target selectLocator;
    private final String optionText;

    private SelectFromAntdDropdown(Target selectLocator, String optionText) {
        this.selectLocator = selectLocator;
        this.optionText = optionText;
    }

    public static SelectFromAntdDropdown withOption(String optionText) {
        return new SelectFromAntdDropdown(null, optionText);
    }

    public SelectFromAntdDropdown from(Target select) {
        return new SelectFromAntdDropdown(select, optionText);
    }

    @Override
    @Step("{0} selecciona '#optionText' del dropdown de Ant Design")
    public <T extends Actor> void performAs(T actor) {
        if (selectLocator != null) {
            actor.attemptsTo(Click.on(selectLocator));
        }

        // Esperar a que el dropdown sea visible
        try {
            Thread.sleep(400);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        // Buscar la opcion por titulo (atributo title de Ant Design) o por texto
        String optionSelector = ".ant-select-dropdown:not(.ant-select-dropdown-hidden) " +
            ".ant-select-item-option[title='" + optionText + "']";
        String optionSelectorFallback = ".ant-select-dropdown:not(.ant-select-dropdown-hidden) " +
            ".ant-select-item-option:contains('" + optionText + "')";

        Target optionTarget = Target.the("opcion '" + optionText + "'")
            .locatedBy(optionSelector);

        actor.attemptsTo(Click.on(optionTarget));
    }
}
