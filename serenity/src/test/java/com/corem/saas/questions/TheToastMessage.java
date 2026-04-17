package com.corem.saas.questions;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.annotations.Subject;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Question: Obtiene el texto del mensaje toast de Ant Design.
 *
 * Los toasts de Ant Design (message.success, message.error) aparecen
 * en elementos .ant-message-notice-content. Esta question espera
 * que aparezca un toast y devuelve su texto.
 */
@Subject("el mensaje toast de Ant Design")
public class TheToastMessage implements Question<String> {

    private TheToastMessage() {}

    public static TheToastMessage text() {
        return new TheToastMessage();
    }

    @Override
    public String answeredBy(Actor actor) {
        try {
            return CoremTargets.ANT_MESSAGE_CONTENT
                .resolveFor(actor)
                .getText();
        } catch (Exception e) {
            return "";
        }
    }
}
