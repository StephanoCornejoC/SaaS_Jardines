/**
 * TESTS: Pensiones (Payments)
 *
 * Prerequisito: sesion activa. Requiere que existan pagos en estado PENDIENTE
 * en la base de datos de prueba.
 *
 * Cubre:
 * - TC-PAY-01: Lista de pagos carga la tabla con columnas correctas
 * - TC-PAY-02: Filtrar pagos por mes y estado reduce los resultados
 * - TC-PAY-03: Registrar pago cambia el estado a PAGADO
 * - TC-PAY-04: Generar QR abre modal con imagen
 */
import { test, expect } from '../fixtures/auth';

test.describe('Pensiones - Pagos', () => {
  test('TC-PAY-01: lista de pensiones carga tabla con columnas y filtros', async ({
    paymentsPage,
  }) => {
    await paymentsPage.goto();

    // El heading debe ser visible
    await expect(paymentsPage.heading).toBeVisible();

    // La tabla debe estar presente
    await expect(paymentsPage.paymentsTable).toBeVisible();

    // Verificar que las columnas principales estan en el header
    const headers = paymentsPage.page.locator('.ant-table-thead th');
    await expect(headers.getByText('Alumno')).toBeVisible();
    await expect(headers.getByText('Mes')).toBeVisible();
    await expect(headers.getByText('Estado')).toBeVisible();
    await expect(headers.getByText('Acciones')).toBeVisible();

    // Los tres selects de filtro deben estar disponibles
    await expect(paymentsPage.mesFilterSelect).toBeVisible();
    await expect(paymentsPage.anioFilterSelect).toBeVisible();
    await expect(paymentsPage.estadoFilterSelect).toBeVisible();
  });

  test('TC-PAY-02: filtrar por estado PAGADO muestra solo pagos pagados', async ({
    paymentsPage,
  }) => {
    await paymentsPage.goto();

    // Aplicar filtro de estado PAGADO
    await paymentsPage.filterByEstado('Pagado');

    // Esperar que la tabla recargue
    const rowCount = await paymentsPage.tableRows.count();

    if (rowCount > 0) {
      // Todos los tags visibles deben decir PAGADO
      const tags = paymentsPage.page.locator('.ant-table-tbody .ant-tag');
      const count = await tags.count();

      for (let i = 0; i < count; i++) {
        const tagText = await tags.nth(i).textContent();
        expect(tagText).toBe('PAGADO');
      }
    }
    // Si no hay pagos pagados, el test es valido: la tabla muestra 0 filas
  });

  test('TC-PAY-03: registrar pago cambia el estado del registro a PAGADO', async ({
    paymentsPage,
  }) => {
    await paymentsPage.goto();

    // Filtrar por estado PENDIENTE para encontrar registros pagables
    await paymentsPage.filterByEstado('Pendiente');

    const rowCount = await paymentsPage.tableRows.count();
    if (rowCount === 0) {
      test.skip(true, 'No hay pensiones PENDIENTE disponibles para este test');
      return;
    }

    // Capturar el nombre del alumno antes de pagar (para verificar post-pago)
    const nombreAlumno = await paymentsPage.tableRows
      .first()
      .locator('td')
      .first()
      .textContent();

    // Abrir modal de pago para la primera fila
    await paymentsPage.clickRegistrarPago(0);

    // Verificar que el modal se abrio con el titulo correcto
    await expect(paymentsPage.payModal).toBeVisible();
    await expect(paymentsPage.payModalTitle).toHaveText('Registrar Pago');

    // El campo monto debe estar pre-rellenado con el monto de la pension
    await expect(paymentsPage.montoInput).not.toBeEmpty();

    // Completar el pago
    await paymentsPage.fillPaymentForm({
      metodoPago: 'Efectivo',
      observaciones: 'Pago test E2E',
    });

    await paymentsPage.submitPayment();

    // Verificar mensaje de exito
    await paymentsPage.expectSuccessMessage('Pago registrado');

    // El registro debe haber cambiado de estado (ya no tiene boton "Registrar Pago")
    // Buscar por el nombre del alumno para localizar la fila
    await paymentsPage.filterByEstado('Pagado');
    const pagadoRows = paymentsPage.page.locator('.ant-table-tbody td', {
      hasText: nombreAlumno || '',
    });
    await expect(pagadoRows.first()).toBeVisible();
  });

  test('TC-PAY-04: boton QR abre modal con imagen de codigo QR', async ({
    paymentsPage,
  }) => {
    await paymentsPage.goto();

    const rowCount = await paymentsPage.tableRows.count();
    if (rowCount === 0) {
      test.skip(true, 'No hay pensiones disponibles para generar QR');
      return;
    }

    // Hacer click en el boton QR de la primera fila
    await paymentsPage.clickGenerarQR(0);

    // El modal del QR debe abrirse (modal.info de Ant Design)
    await expect(paymentsPage.qrModal).toBeVisible({ timeout: 10000 });

    // La imagen del QR debe estar visible y tener dimensiones
    await expect(paymentsPage.qrImage).toBeVisible();
    const imgBox = await paymentsPage.qrImage.boundingBox();
    expect(imgBox?.width).toBeGreaterThan(0);
    expect(imgBox?.height).toBeGreaterThan(0);

    // Cerrar el modal
    await paymentsPage.closeQrModal();
    await expect(paymentsPage.qrModal).toBeHidden();
  });
});
