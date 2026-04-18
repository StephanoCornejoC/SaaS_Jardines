/**
 * TESTS: Caja (Cashflow)
 *
 * Prerequisito: sesion activa con rol que tenga acceso a /caja.
 *
 * Cubre:
 * - TC-CASH-01: Dashboard financiero muestra estadisticas de ingresos/egresos/balance
 * - TC-CASH-02: Registrar nueva transaccion de tipo INGRESO aparece en la tabla
 * - TC-CASH-03: Tab de Cierres Mensuales muestra la tabla de cierres
 */
import { test, expect } from '../fixtures/auth';

test.describe('Flujo de Caja', () => {
  test('TC-CASH-01: cards de resumen muestran ingresos, egresos y balance del mes', async ({
    cashflowPage,
  }) => {
    await cashflowPage.goto();

    // Los tres Statistic cards deben ser visibles
    await expect(cashflowPage.statIngresos).toBeVisible();
    await expect(cashflowPage.statEgresos).toBeVisible();
    await expect(cashflowPage.statBalance).toBeVisible();

    // Los valores deben ser numericos (pueden ser 0 si no hay datos)
    const ingresos = await cashflowPage.getStatValue(cashflowPage.statIngresos);
    const egresos = await cashflowPage.getStatValue(cashflowPage.statEgresos);
    const balance = await cashflowPage.getStatValue(cashflowPage.statBalance);

    expect(ingresos).toBeGreaterThanOrEqual(0);
    expect(egresos).toBeGreaterThanOrEqual(0);
    // El balance puede ser negativo, pero debe ser numerico
    expect(typeof balance).toBe('number');

    // El tab de Transacciones debe estar activo por defecto
    await expect(cashflowPage.tabTransacciones).toHaveClass(/ant-tabs-tab-active/);
  });

  test('TC-CASH-02: crear nueva transaccion INGRESO la agrega a la tabla', async ({
    cashflowPage,
  }) => {
    await cashflowPage.goto();

    // Capturar el numero de transacciones antes
    const countBefore = await cashflowPage.getTransactionCount();

    // Abrir modal de nueva transaccion
    await cashflowPage.openNewTransactionModal();
    await expect(cashflowPage.modal).toBeVisible();

    const descripcionUnica = `Test E2E Ingreso ${Date.now()}`;

    // Llenar el formulario de transaccion
    await cashflowPage.fillTransactionForm({
      tipo: 'Ingreso',
      categoria: 'Pensiones',
      descripcion: descripcionUnica,
      monto: 150.5,
      fecha: '08/04/2026',
    });

    // Guardar
    await cashflowPage.submitTransaction();

    // Verificar mensaje de exito
    await cashflowPage.expectSuccessMessage('Transaccion registrada');

    // La tabla debe tener una fila mas
    const countAfter = await cashflowPage.getTransactionCount();
    expect(countAfter).toBe(countBefore + 1);

    // La descripcion debe aparecer en la tabla
    await cashflowPage.expectTransactionInTable(descripcionUnica);
  });

  test('TC-CASH-03: formulario de transaccion valida campos requeridos', async ({
    cashflowPage,
  }) => {
    await cashflowPage.goto();
    await cashflowPage.openNewTransactionModal();

    // Intentar guardar sin llenar nada
    await cashflowPage.modalOkButton.click();

    // Todos los campos requeridos deben mostrar error
    await cashflowPage.expectModalValidationError('Tipo');
    await cashflowPage.expectModalValidationError('Categoria');
    await cashflowPage.expectModalValidationError('Descripcion');
    await cashflowPage.expectModalValidationError('Monto');
    await cashflowPage.expectModalValidationError('Fecha');

    // El modal no debe cerrarse
    await expect(cashflowPage.modal).toBeVisible();

    // Cancelar
    await cashflowPage.modal
      .locator('.ant-modal-footer button:not(.ant-btn-primary)')
      .click();
    await expect(cashflowPage.modal).toBeHidden();
  });

  test('TC-CASH-04: tab de Cierres Mensuales muestra la tabla de cierres historicos', async ({
    cashflowPage,
  }) => {
    await cashflowPage.goto();

    // Navegar al tab de cierres
    await cashflowPage.clickTabCierres();

    // El tab debe estar activo
    await expect(cashflowPage.tabCierres).toHaveClass(/ant-tabs-tab-active/);

    // La tabla de cierres debe estar visible
    await expect(cashflowPage.closuresTable).toBeVisible();

    // Los headers de la tabla de cierres deben estar presentes
    const headers = cashflowPage.page.locator('.ant-tabs-tabpane-active .ant-table-thead th');
    await expect(headers.getByText('Mes')).toBeVisible();
    await expect(headers.getByText('Ano')).toBeVisible();
    await expect(headers.getByText('Total Ingresos')).toBeVisible();
    await expect(headers.getByText('Total Egresos')).toBeVisible();
    await expect(headers.getByText('Balance')).toBeVisible();
    await expect(headers.getByText('Estado')).toBeVisible();
  });
});
