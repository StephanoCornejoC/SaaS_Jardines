package com.corem.saas.abilities;

import com.corem.saas.helpers.CoremApiClient;
import net.serenitybdd.screenplay.Ability;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;

/**
 * Ability que permite al actor llamar a la API REST de COREM.
 *
 * Se usa principalmente para configurar datos de prueba (Given/Dado que)
 * sin depender de la UI, lo que hace los tests mas robustos y rapidos.
 *
 * Uso:
 *   actor.whoCan(CallTheCoremApi.as("admin@test.com", "TestPass1234"));
 *   CoremApiClient api = CallTheCoremApi.as(actor);
 */
public class CallTheCoremApi implements Ability {

    private final CoremApiClient apiClient;

    private CallTheCoremApi(CoremApiClient apiClient) {
        this.apiClient = apiClient;
    }

    /**
     * Crea la ability con credenciales especificas.
     */
    public static CallTheCoremApi using(String baseUrl, String tenantHost, String email, String password) {
        return new CallTheCoremApi(new CoremApiClient(baseUrl, tenantHost, email, password));
    }

    /**
     * Crea la ability con configuracion del entorno local por defecto.
     */
    public static CallTheCoremApi forLocalEnvironment() {
        return new CallTheCoremApi(CoremApiClient.forLocalEnvironment());
    }

    /**
     * Recupera la ability de un actor.
     */
    public static CoremApiClient as(Actor actor) {
        return actor.abilityTo(CallTheCoremApi.class).apiClient;
    }

    /**
     * Recupera el API client directamente.
     */
    public CoremApiClient getApiClient() {
        return apiClient;
    }

    @Override
    public String toString() {
        return "llamar a la API de COREM";
    }
}
