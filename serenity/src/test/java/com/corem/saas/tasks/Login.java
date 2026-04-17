package com.corem.saas.tasks;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.screenplay.actions.Open;
import net.serenitybdd.annotations.Step;

/**
 * Task: Login en SAAS COREM.
 *
 * Encapsula el flujo completo de autenticacion:
 * 1. Navegar a /login
 * 2. Ingresar email y contrasena
 * 3. Hacer clic en el boton de ingresar
 *
 * Uso:
 *   actor.attemptsTo(Login.withCredentials("admin@test.com", "TestPass1234"));
 */
public class Login implements Task {

    private final String email;
    private final String password;

    private Login(String email, String password) {
        this.email = email;
        this.password = password;
    }

    public static Login withCredentials(String email, String password) {
        return new Login(email, password);
    }

    public static Login withDefaultCredentials() {
        return new Login("admin@test.com", "TestPass1234");
    }

    @Override
    @Step("{0} inicia sesion con email '#email'")
    public <T extends Actor> void performAs(T actor) {
        actor.attemptsTo(
            Open.url("/login"),
            Enter.theValue(email).into(CoremTargets.LOGIN_EMAIL_INPUT),
            Enter.theValue(password).into(CoremTargets.LOGIN_PASSWORD_INPUT),
            Click.on(CoremTargets.LOGIN_SUBMIT_BUTTON)
        );
    }
}
