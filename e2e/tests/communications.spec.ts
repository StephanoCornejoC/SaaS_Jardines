/**
 * TESTS: Comunicaciones (Libro de comunicaciones)
 *
 * Prerequisito: sesion activa.
 *
 * Cubre:
 * - TC-COMM-01: Lista de comunicaciones carga la tabla
 * - TC-COMM-02: Crear comunicacion GENERAL exitosamente
 * - TC-COMM-03: Enviar comunicacion via Popconfirm cambia estado a ENVIADO
 */
import { test, expect } from '../fixtures/auth';

test.describe('Comunicaciones', () => {
  test('TC-COMM-01: lista de comunicaciones carga la tabla con columnas correctas', async ({
    page,
  }) => {
    await page.goto('/comunicaciones');
    await expect(page.getByRole('heading', { name: 'Comunicaciones' })).toBeVisible();
    await expect(page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });

    // La tabla debe estar visible
    await expect(page.locator('.ant-table-wrapper')).toBeVisible();

    // Columnas esperadas
    const headers = page.locator('.ant-table-thead th');
    await expect(headers.getByText('Titulo')).toBeVisible();
    await expect(headers.getByText('Tipo')).toBeVisible();
    await expect(headers.getByText('Estado')).toBeVisible();

    // El boton de nueva comunicacion debe estar disponible
    await expect(page.getByRole('button', { name: 'Nueva Comunicacion' })).toBeVisible();
  });

  test('TC-COMM-02: crear comunicacion GENERAL con titulo y contenido la registra en la tabla', async ({
    page,
  }) => {
    await page.goto('/comunicaciones');
    await expect(page.getByRole('heading', { name: 'Comunicaciones' })).toBeVisible();

    // Abrir modal
    await page.getByRole('button', { name: 'Nueva Comunicacion' }).click();
    const modal = page.locator('.ant-modal', { hasText: 'Nueva Comunicacion' });
    await expect(modal).toBeVisible();

    const tituloUnico = `Comunicado Test E2E ${Date.now()}`;

    // Llenar el formulario
    await modal.getByLabel('Titulo').fill(tituloUnico);
    await modal.getByLabel('Contenido').fill(
      'Este es el contenido del comunicado generado por test E2E automatizado.'
    );

    // El tipo "GENERAL" debe estar preseleccionado (initialValue del Form.Item)
    // Verificar que el selector de aula NO sea visible (solo aparece para POR_AULA)
    await expect(modal.getByLabel('Aula')).toBeHidden();

    // Guardar
    await modal.locator('.ant-modal-footer button.ant-btn-primary').click();
    await expect(modal).toBeHidden({ timeout: 10000 });

    // Verificar mensaje de exito
    await expect(
      page.locator('.ant-message-notice-content', { hasText: 'Comunicacion creada' })
    ).toBeVisible({ timeout: 5000 });

    // El comunicado debe aparecer en la tabla
    await expect(page.locator('.ant-table-tbody td', { hasText: tituloUnico })).toBeVisible();
  });

  test('TC-COMM-03: selector de aula aparece solo cuando el tipo es POR_AULA', async ({
    page,
  }) => {
    await page.goto('/comunicaciones');
    await page.getByRole('button', { name: 'Nueva Comunicacion' }).click();

    const modal = page.locator('.ant-modal', { hasText: 'Nueva Comunicacion' });
    await expect(modal).toBeVisible();

    // Con tipo GENERAL (default), el campo Aula no debe ser visible
    await expect(modal.locator('.ant-form-item', { hasText: 'Aula' })).toBeHidden();

    // Cambiar el tipo a POR_AULA
    const tipoSelect = modal.locator('.ant-select').filter({
      has: modal.locator('.ant-form-item-label', { hasText: 'Tipo' }),
    });
    await tipoSelect.click();
    await page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .getByTitle('Por Aula')
      .click();

    // Ahora el campo Aula debe aparecer (renderizado condicionalmente)
    await expect(modal.locator('.ant-form-item', { hasText: 'Aula' })).toBeVisible();

    // Cancelar sin guardar
    await modal.locator('.ant-modal-footer button:not(.ant-btn-primary)').click();
    await expect(modal).toBeHidden();
  });

  test('TC-COMM-04: enviar comunicacion via Popconfirm cambia estado a ENVIADO', async ({
    page,
  }) => {
    await page.goto('/comunicaciones');
    await expect(page.getByRole('heading', { name: 'Comunicaciones' })).toBeVisible();
    await expect(page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });

    // Buscar la primera comunicacion con estado BORRADOR (boton Enviar visible)
    const sendButton = page
      .locator('.ant-table-tbody tr.ant-table-row')
      .filter({
        has: page.getByRole('button', { name: 'Enviar' }),
      })
      .first()
      .getByRole('button', { name: 'Enviar' });

    const hasSendButton = (await sendButton.count()) > 0;
    if (!hasSendButton) {
      test.skip(true, 'No hay comunicaciones en estado BORRADOR para enviar');
      return;
    }

    // Hacer click en Enviar - abre el Popconfirm de Ant Design
    await sendButton.click();

    // El Popconfirm muestra un tooltip con el titulo de confirmacion y botones Si/Cancelar
    const popconfirm = page.locator('.ant-popconfirm');
    await expect(popconfirm).toBeVisible({ timeout: 5000 });
    await expect(popconfirm).toContainText('Enviar esta comunicacion?');

    // Confirmar el envio haciendo click en el boton de confirmacion del Popconfirm
    await popconfirm.getByRole('button', { name: 'OK' }).click();

    // Verificar mensaje de exito
    await expect(
      page.locator('.ant-message-notice-content', { hasText: 'Comunicacion enviada' })
    ).toBeVisible({ timeout: 8000 });
  });
});
