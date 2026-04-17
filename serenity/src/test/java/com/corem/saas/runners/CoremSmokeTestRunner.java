package com.corem.saas.runners;

import io.cucumber.junit.platform.engine.Constants;
import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

/**
 * Runner de Smoke Tests: ejecuta solo los TC-XX-01 de cada modulo.
 * Util para verificacion rapida post-deploy (~5 minutos).
 *
 * Ejecutar: mvn verify -Pcucumber.filter.tags="@tc-auth-01 or @tc-stu-01 or @tc-pay-01 or @tc-att-01 or @tc-cash-01 or @tc-dash-01 or @tc-comm-01 or @tc-rep-01 or @tc-nav-01"
 */
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = Constants.GLUE_PROPERTY_NAME, value = "com.corem.saas.stepdefinitions")
@ConfigurationParameter(key = Constants.PLUGIN_PROPERTY_NAME,
    value = "pretty," +
            "html:target/cucumber-reports/smoke-report.html," +
            "io.cucumber.core.plugin.SerenityReporterParallel")
@ConfigurationParameter(key = Constants.FEATURES_PROPERTY_NAME, value = "src/test/resources/features")
@ConfigurationParameter(key = Constants.FILTER_TAGS_PROPERTY_NAME,
    value = "@tc-auth-01 or @tc-stu-01 or @tc-pay-01 or @tc-att-01 or @tc-cash-01 or @tc-dash-01 or @tc-comm-01 or @tc-rep-01 or @tc-nav-01")
public class CoremSmokeTestRunner {
    // Smoke tests: TC-XX-01 de cada modulo
}
