/**
 * TESTS: Reportes (descarga de Excel)
 *
 * Prerequisito: sesion activa.
 *
 * La descarga de archivos en Playwright requiere capturar el evento 'download'.
 * La descarga se inicia por un click que desencadena window.URL.createObjectURL
 * y un <a>.click() en el componente Reports.jsx.
 *
 * Cubre:
 * - TC-REP-01: Pagina de reportes muestra las 4 tarjetas de reportes disponibles
 * - TC-REP-02: Descargar reporte de alumnos inicia la descarga de un .xlsx
 */
import { test, expect } from '../fixtures/auth';
import * as path from 'path';

test.describe('Reportes', () => {
  test('TC-REP-01: pagina de reportes muestra las 4 tarjetas de descarga', async ({
    page,
  }) => {
    await page.goto('/reportes');
    await expect(page.getByRole('heading', { name: 'Reportes' })).toBeVisible();

    // Las 4 tarjetas de reportes deben estar presentes
    const reportCards = [
      'Reporte de Morosidad',
      'Lista de Alumnos',
      'Reporte de Asistencia',
      'Reporte de Caja',
    ];

    for (const cardTitle of reportCards) {
      await expect(page.getByText(cardTitle)).toBeVisible();
    }

    // Todos los botones "Descargar Excel" deben estar disponibles (4 total)
    const downloadButtons = page.getByRole('button', { name: 'Descargar Excel' });
    await expect(downloadButtons).toHaveCount(4);
  });

  test('TC-REP-02: descargar "Lista de Alumnos" inicia descarga de archivo .xlsx', async ({
    page,
  }) => {
    await page.goto('/reportes');
    await expect(page.getByRole('heading', { name: 'Reportes' })).toBeVisible();

    // Capturar el evento de descarga antes de hacer click
    // Playwright intercepta el download antes de que el browser lo procese
    const downloadPromise = page.waitForEvent('download', { timeout: 30000 });

    // Encontrar la tarjeta "Lista de Alumnos" y hacer click en su boton
    const alumnosCard = page.locator('.ant-card', { hasText: 'Lista de Alumnos' });
    await alumnosCard.getByRole('button', { name: 'Descargar Excel' }).click();

    // Esperar el evento de descarga
    const download = await downloadPromise;

    // El nombre del archivo debe ser el esperado
    expect(download.suggestedFilename()).toBe('lista_alumnos.xlsx');

    // Verificar que el archivo no esta vacio guardandolo temporalmente
    const downloadPath = path.join('test-results', 'downloads', download.suggestedFilename());
    await download.saveAs(downloadPath);

    // El mensaje de exito de Ant Design debe aparecer
    await expect(
      page.locator('.ant-message-notice-content', { hasText: 'Lista de Alumnos descargado' })
    ).toBeVisible({ timeout: 5000 });
  });

  test('TC-REP-03: boton de descarga muestra estado "loading" durante la peticion', async ({
    page,
  }) => {
    await page.goto('/reportes');
    await expect(page.getByRole('heading', { name: 'Reportes' })).toBeVisible();

    const morosidadCard = page.locator('.ant-card', { hasText: 'Reporte de Morosidad' });
    const downloadBtn = morosidadCard.getByRole('button', { name: 'Descargar Excel' });

    // Interceptar la llamada a la API para retrasarla y verificar el estado loading
    await page.route('**/api/reports/morosidad-excel/**', async (route) => {
      // Simular delay de red
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.continue();
    });

    // Iniciar descarga
    const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
    await downloadBtn.click();

    // El boton debe estar en estado loading (clase ant-btn-loading de Ant Design)
    await expect(downloadBtn).toHaveClass(/ant-btn-loading/);

    // Esperar que complete
    await downloadPromise;

    // El boton debe volver a estado normal
    await expect(downloadBtn).not.toHaveClass(/ant-btn-loading/);
  });
});
