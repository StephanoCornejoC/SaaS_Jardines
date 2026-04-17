package com.corem.saas.stepdefinitions;

import com.corem.saas.helpers.TestDataStore;
import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.Scenario;
import net.thucydides.core.webdriver.ThucydidesWebDriverSupport;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Hooks globales de Cucumber para SAAS COREM E2E Tests.
 *
 * Responsabilidades:
 * - Inicializar el contexto del escenario antes de cada test
 * - Limpiar recursos (datos de test, contexto del actor) despues de cada test
 * - Capturar screenshot en caso de fallo
 */
public class CucumberHooks {

    private static final Logger log = LoggerFactory.getLogger(CucumberHooks.class);

    @Before(order = 0)
    public void beforeScenario(Scenario scenario) {
        log.info("========================================");
        log.info("Iniciando escenario: {}", scenario.getName());
        log.info("Tags: {}", scenario.getSourceTagNames());
        log.info("========================================");

        // Limpiar el contexto del actor para que cada escenario sea independiente
        ScenarioContext.reset();

        // Limpiar el store de datos de prueba
        TestDataStore.getInstance().clear();
    }

    @After(order = 0)
    public void afterScenario(Scenario scenario) {
        if (scenario.isFailed()) {
            log.error("FALLO en escenario: {}", scenario.getName());
            // Serenity ya captura screenshots automaticamente en fallos
            // cuando se configura take.screenshots = FOR_FAILURES
        } else {
            log.info("Escenario completado exitosamente: {}", scenario.getName());
        }

        // Limpiar datos de prueba del escenario
        TestDataStore.getInstance().clear();

        // Resetear el contexto del actor
        ScenarioContext.reset();
    }
}
