/**
 * TESTS: Dashboard
 *
 * Verifica que los KPIs y el grafico se renderizan correctamente
 * tras el fetch a /dashboard/resumen/.
 *
 * Cubre:
 * - TC-DASH-01: Todos los KPIs son visibles con valores numericos
 * - TC-DASH-02: El grafico de ingresos mensuales se renderiza (canvas con dimensiones)
 */
import { test, expect } from '../fixtures/auth';

test.describe('Dashboard', () => {
  test('TC-DASH-01: los cuatro KPIs se muestran con titulos y valores numericos', async ({
    dashboardPage,
  }) => {
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardReady();

    // Todos los KPIs deben ser visibles
    await dashboardPage.expectAllKpisVisible();

    // Los valores de los KPIs deben ser numericos (no NaN, no texto de error)
    const totalAlumnos = await dashboardPage.getKpiValue(dashboardPage.kpiTotalAlumnos);
    const totalProfesores = await dashboardPage.getKpiValue(dashboardPage.kpiTotalProfesores);
    const ingresosMes = await dashboardPage.getKpiValue(dashboardPage.kpiIngresosMes);
    const morosidad = await dashboardPage.getKpiValue(dashboardPage.kpiMorosidad);

    // Convertir a numero y verificar que son valores validos (>= 0)
    expect(parseFloat(totalAlumnos.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);
    expect(parseFloat(totalProfesores.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);
    expect(parseFloat(ingresosMes.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);
    expect(parseFloat(morosidad.replace(/,/g, ''))).toBeGreaterThanOrEqual(0);

    // La barra lateral con el menu debe estar visible
    await expect(dashboardPage.sidebarMenu).toBeVisible();
  });

  test('TC-DASH-02: el grafico de ingresos mensuales se renderiza correctamente', async ({
    dashboardPage,
  }) => {
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardReady();

    // Verificar que el canvas del grafico Chart.js se renderizo
    await dashboardPage.expectChartRendered();

    // El card contenedor del grafico debe estar visible
    const chartCard = dashboardPage.page.locator('.ant-card').last();
    await expect(chartCard).toBeVisible();
  });
});
