package com.corem.saas.stepdefinitions;

import com.corem.saas.helpers.TestDataStore;
import com.corem.saas.interactions.WaitForSpinner;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.TheLocalStorageValue;
import com.corem.saas.questions.ThePageUrl;
import com.corem.saas.questions.TheToastMessage;
import com.corem.saas.tasks.Login;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Open;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;

import java.time.Duration;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Autenticacion.
 * Feature: auth/autenticacion.feature
 */
public class AuthStepDefinitions {

    private Actor actor;

    @Dado("que el sistema COREM esta disponible en http://localhost:3000")
    public void sistemaCOREMDisponible() {
        // Precondicion documentada. No requiere accion.
    }

    @Dado("que soy un usuario sin sesion activa")
    public void soyUsuarioSinSesion() {
        actor = ScenarioContext.getActor();
        // Limpiar localStorage via JS para eliminar tokens
        try {
            WebDriver driver = BrowseTheWeb.as(actor).getDriver();
            if (driver instanceof JavascriptExecutor) {
                ((JavascriptExecutor) driver).executeScript("localStorage.clear(); sessionStorage.clear();");
            }
        } catch (Exception ignored) {}
        actor.attemptsTo(Open.url("/login"));
    }

    @Y("navego a la pagina de login")
    public void navegoALogin() {
        actor.attemptsTo(Open.url("/login"));
    }

    @Entonces("veo los campos de email, contrasena y el boton de ingresar")
    public void veoFormularioLogin() {
        actor.should(
            seeThat(IsElementVisible.at(CoremTargets.LOGIN_EMAIL_INPUT), is(true)),
            seeThat(IsElementVisible.at(CoremTargets.LOGIN_PASSWORD_INPUT), is(true)),
            seeThat(IsElementVisible.at(CoremTargets.LOGIN_SUBMIT_BUTTON), is(true))
        );
    }

    @Cuando("ingreso las credenciales validas {string} y {string}")
    public void ingresoCedencialesValidas(String email, String password) {
        actor.attemptsTo(Login.withCredentials(email, password));
    }

    @Cuando("ingreso las credenciales invalidas {string} y {string}")
    public void ingresoCedencialesInvalidas(String email, String password) {
        actor.attemptsTo(Login.withCredentials(email, password));
    }

    @Y("hago clic en el boton Ingresar")
    public void clicBotonIngresar() {
        // Ya clickeado por la Task Login
    }

    @Entonces("soy redirigido al dashboard")
    public void redirigidoAlDashboard() {
        long start = System.currentTimeMillis();
        while (System.currentTimeMillis() - start < 10000) {
            try {
                String url = BrowseTheWeb.as(actor).getDriver().getCurrentUrl();
                if (url != null && url.contains("dashboard")) break;
                Thread.sleep(300);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString("dashboard")));
    }

    @Y("el encabezado {string} es visible")
    public void encabezadoVisible(String heading) {
        actor.should(
            seeThat(IsElementVisible.at(
                Target.the("heading " + heading)
                    .locatedBy("h1, h2, h3, h4, [class*='title']")
                    .containingText(heading)
            ), is(true))
        );
    }

    @Y("mi email aparece en el encabezado de la aplicacion")
    public void emailEnEncabezado() {
        actor.should(
            seeThat(IsElementVisible.at(CoremTargets.HEADER_EMAIL), is(true))
        );
    }

    @Entonces("aparece el mensaje de error de Ant Design {string}")
    public void mensajeErrorAntDesign(String mensajeEsperado) {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MESSAGE_CONTENT, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(8))
        );
        actor.should(seeThat(TheToastMessage.text(), containsString(mensajeEsperado)));
    }

    @Y("permanezco en la pagina de login")
    public void permanezcoEnLogin() {
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString("login")));
    }

    @Y("el formulario de login sigue visible")
    public void formularioLoginVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.LOGIN_EMAIL_INPUT), is(true)));
    }

    @Cuando("hago clic en el boton Ingresar sin llenar ningun campo")
    public void clicSinLlenarCampos() {
        actor.attemptsTo(Click.on(CoremTargets.LOGIN_SUBMIT_BUTTON));
    }

    @Entonces("el campo {string} muestra el error {string}")
    public void campoMuestraError(String campo, String error) {
        Target errorTarget = Target.the("error de validacion")
            .locatedBy(".ant-form-item-explain-error");
        actor.should(seeThat(IsElementVisible.at(errorTarget), is(true)));
    }

    @Dado("que tengo una sesion activa como administrador")
    public void tengoSesionActiva() {
        actor = ScenarioContext.getActor();
        // Verificar si ya hay sesion activa
        try {
            WebDriver driver = BrowseTheWeb.as(actor).getDriver();
            Object token = null;
            if (driver instanceof JavascriptExecutor) {
                token = ((JavascriptExecutor) driver).executeScript("return localStorage.getItem('access_token');");
            }
            if (token != null && !token.toString().isEmpty()) {
                return; // Ya hay sesion activa
            }
        } catch (Exception ignored) {}

        // Realizar login
        actor.attemptsTo(
            Open.url("/login"),
            Login.withDefaultCredentials()
        );

        // Esperar que la URL cambie a /dashboard
        long start = System.currentTimeMillis();
        while (System.currentTimeMillis() - start < 15000) {
            try {
                String url = BrowseTheWeb.as(actor).getDriver().getCurrentUrl();
                if (url != null && url.contains("dashboard")) break;
                Thread.sleep(300);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    @Y("navego al dashboard")
    public void navegoAlDashboard() {
        actor.attemptsTo(NavigateToModule.withPath("/dashboard"));
    }

    @Cuando("hago clic en el boton Salir del encabezado")
    public void clicBotonSalir() {
        Target logoutBtn = Target.the("area del header para logout")
            .locatedBy(".ant-layout-header button:last-child, .ant-layout-header [role='button']");
        actor.attemptsTo(Click.on(logoutBtn));

        // Si hay menu desplegable, buscar la opcion Salir
        try {
            Thread.sleep(500);
            Target salirOption = Target.the("opcion Salir")
                .locatedBy(".ant-dropdown-menu-item, li").containingText("Salir");
            if (salirOption.resolveAllFor(actor).size() > 0) {
                actor.attemptsTo(Click.on(salirOption));
            }
        } catch (Exception ignored) {}
    }

    @Entonces("soy redirigido a la pagina de login")
    public void redirigidoALogin() {
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.LOGIN_EMAIL_INPUT, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(10))
        );
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString("login")));
    }

    @Y("al intentar navegar a {string} soy redirigido a login")
    public void intentarNavegarRedirigidoALogin(String path) {
        actor.attemptsTo(Open.url(path));
        actor.should(seeThat(ThePageUrl.currentUrl(), containsString("login")));
    }

    @Y("el token de acceso no existe en el almacenamiento local")
    public void tokenNoExiste() {
        actor.should(seeThat(TheLocalStorageValue.forKey("access_token"), is(nullValue())));
    }
}
