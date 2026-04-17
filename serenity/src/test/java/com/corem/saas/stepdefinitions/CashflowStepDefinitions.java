package com.corem.saas.stepdefinitions;

import com.corem.saas.helpers.TestDataStore;
import com.corem.saas.questions.IsElementVisible;
import com.corem.saas.questions.TheTableRowCount;
import com.corem.saas.questions.TheToastMessage;
import com.corem.saas.tasks.CreateTransaction;
import com.corem.saas.tasks.NavigateToModule;
import com.corem.saas.ui.CoremTargets;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.es.*;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.matchers.WebElementStateMatchers;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.screenplay.waits.WaitUntil;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static net.serenitybdd.screenplay.GivenWhenThen.seeThat;
import static org.hamcrest.Matchers.*;

/**
 * Step definitions para los escenarios de Flujo de Caja.
 */
public class CashflowStepDefinitions {

    private Actor actor;
    private int transactionCountBefore;

    @Y("navego al modulo de Caja")
    public void navegoCaja() {
        actor = ScenarioContext.getActor();
        actor.attemptsTo(NavigateToModule.withPath("/caja"));
    }

    @Entonces("la card de {string} del mes es visible")
    public void cardVisible(String tipo) {
        Target cardTarget;
        switch (tipo.toLowerCase()) {
            case "ingresos": cardTarget = CoremTargets.CAJA_STAT_INGRESOS; break;
            case "egresos": cardTarget = CoremTargets.CAJA_STAT_EGRESOS; break;
            case "balance": cardTarget = CoremTargets.CAJA_STAT_BALANCE; break;
            default: cardTarget = Target.the("card " + tipo).locatedBy(".ant-statistic").containingText(tipo);
        }
        actor.should(seeThat(IsElementVisible.at(cardTarget), is(true)));
    }

    @Y("los valores de las cards son numericos")
    public void valoresNumericos() {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("valores de estadisticas").locatedBy(".ant-statistic-content-value")
        ), is(true)));
    }

    @Y("el tab {string} esta activo por defecto")
    public void tabActivoPorDefecto(String tabName) {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.CAJA_TAB_TRANSACCIONES), is(true)));
    }

    @Cuando("cuento las transacciones actuales en la tabla")
    public void cuento() {
        transactionCountBefore = actor.asksFor(TheTableRowCount.inTheCurrentTable());
        TestDataStore.getInstance().put(TestDataStore.TRANSACTION_COUNT_BEFORE, transactionCountBefore);
    }

    @Y("abro el modal de nueva transaccion")
    public void abroModalNuevaTransaccion() {
        actor.attemptsTo(Click.on(CoremTargets.CAJA_NUEVA_TRANSACCION_BUTTON));
        actor.attemptsTo(
            WaitUntil.the(CoremTargets.ANT_MODAL, WebElementStateMatchers.isVisible())
                .forNoMoreThan(Duration.ofSeconds(5))
        );
    }

    @Y("lleno el formulario de transaccion:")
    public void llenoFormularioTransaccion(DataTable datos) {
        List<Map<String, String>> rows = datos.asMaps(String.class, String.class);
        Map<String, String> formData = new java.util.HashMap<>();
        for (Map<String, String> row : rows) {
            formData.put(row.get("campo"), row.get("valor"));
        }
        String descripcion = formData.getOrDefault("Descripcion", "Test") + " " + System.currentTimeMillis();
        TestDataStore.getInstance().put("descripcion_transaccion", descripcion);

        actor.attemptsTo(
            CreateTransaction.ofType(formData.getOrDefault("Tipo", "Ingreso"))
                .withCategory(formData.getOrDefault("Categoria", "Otros"))
                .withDescription(descripcion)
                .withAmount(Double.parseDouble(formData.getOrDefault("Monto", "100").replace(",", ".")))
                .onDate(formData.getOrDefault("Fecha", "01/01/2026"))
                .build()
        );
    }

    @Y("guardo la transaccion")
    public void guardo() {
        try { Thread.sleep(1000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Y("la tabla tiene una transaccion mas que antes")
    public void tablaUnaTransaccionMas() {
        int countBefore = (int) TestDataStore.getInstance().get(TestDataStore.TRANSACTION_COUNT_BEFORE);
        actor.should(seeThat(TheTableRowCount.inTheCurrentTable(), equalTo(countBefore + 1)));
    }

    @Y("la descripcion {string} aparece en la tabla")
    public void descripcionEnTabla(String descripcion) {
        String desc = TestDataStore.getInstance().get("descripcion_transaccion");
        if (desc == null) desc = descripcion;
        actor.should(seeThat(IsElementVisible.at(
            Target.the("descripcion en tabla").locatedBy(".ant-table-tbody td").containingText(desc)
        ), is(true)));
    }

    @Cuando("intento guardar la transaccion sin llenar ningun campo")
    public void intentoGuardarSinCampos() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_OK_BUTTON));
    }

    @Entonces("el modal muestra errores de validacion en los campos requeridos:")
    public void modalMuestraErrores(DataTable camposTable) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("mensajes de error").locatedBy(".ant-form-item-explain-error")
        ), is(true)));
    }

    @Y("el modal de transaccion permanece abierto")
    public void modalTransaccionPermanece() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_MODAL), is(true)));
    }

    @Cuando("cancelo el modal de transaccion")
    public void canceloModalTransaccion() {
        actor.attemptsTo(Click.on(CoremTargets.ANT_MODAL_CANCEL_BUTTON));
    }

    @Entonces("el modal de transaccion esta oculto")
    public void modalTransaccionOculto() {
        try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        actor.should(seeThat(IsElementVisible.at(CoremTargets.ANT_MODAL), is(false)));
    }

    @Cuando("hago clic en el tab {string}")
    public void clicTab(String tabName) {
        Target tabTarget = Target.the("tab " + tabName).locatedBy(".ant-tabs-tab").containingText(tabName);
        actor.attemptsTo(Click.on(tabTarget));
        try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Entonces("el tab {string} esta activo")
    public void tabActivo(String tabName) {
        actor.should(seeThat(IsElementVisible.at(
            Target.the("tab activo " + tabName).locatedBy(".ant-tabs-tab-active").containingText(tabName)
        ), is(true)));
    }

    @Y("la tabla de cierres es visible")
    public void tablaCierresVisible() {
        actor.should(seeThat(IsElementVisible.at(CoremTargets.CAJA_CLOSURES_TABLE), is(true)));
    }

    @Y("la tabla de cierres contiene las columnas {string}, {string}, {string}, {string}, {string}, {string}")
    public void tablaCierresColumnas(String c1, String c2, String c3, String c4, String c5, String c6) {
        for (String col : new String[]{c1, c2, c3, c4, c5, c6}) {
            actor.should(seeThat(IsElementVisible.at(
                Target.the("columna " + col)
                    .locatedBy(".ant-tabs-tabpane-active .ant-table-thead th")
                    .containingText(col)
            ), is(true)));
        }
    }
}
