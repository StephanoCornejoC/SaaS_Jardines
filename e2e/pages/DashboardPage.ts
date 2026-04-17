/**
 * PAGE OBJECT: Dashboard
 *
 * Componente: src/pages/Dashboard.jsx
 * Ruta: /dashboard
 *
 * Muestra 4 KPIs (Statistic de Ant Design) y un grafico Bar de Chart.js.
 * El canvas del grafico se renderiza via react-chartjs-2.
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="kpi-total-alumnos"      en el Card de Total Alumnos
 *   - data-testid="kpi-total-profesores"   en el Card de Total Profesores
 *   - data-testid="kpi-ingresos-mes"       en el Card de Ingresos del Mes
 *   - data-testid="kpi-morosidad"          en el Card de % Morosidad
 *   - data-testid="chart-ingresos"         en el Card del grafico
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;

  readonly heading: Locator;
  readonly spinnerLoading: Locator;
  // KPIs: Ant Design Statistic tiene un title (texto secundario) y un value
  readonly kpiTotalAlumnos: Locator;
  readonly kpiTotalProfesores: Locator;
  readonly kpiIngresosMes: Locator;
  readonly kpiMorosidad: Locator;
  // Grafico Chart.js renderiza un <canvas>
  readonly ingresosMensualesChart: Locator;
  // Sidebar menu
  readonly sidebarMenu: Locator;
  readonly logoutButton: Locator;
  readonly userEmail: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Dashboard' });
    this.spinnerLoading = page.locator('.ant-spin-spinning');

    // Los Statistic de Ant Design tienen estructura: .ant-statistic-title + .ant-statistic-content
    this.kpiTotalAlumnos = page.locator('.ant-statistic', { hasText: 'Total Alumnos' });
    this.kpiTotalProfesores = page.locator('.ant-statistic', { hasText: 'Total Profesores' });
    this.kpiIngresosMes = page.locator('.ant-statistic', { hasText: 'Ingresos del Mes' });
    this.kpiMorosidad = page.locator('.ant-statistic', { hasText: '% Morosidad' });

    this.ingresosMensualesChart = page.locator('canvas').first();
    this.sidebarMenu = page.locator('.ant-menu');
    this.logoutButton = page.getByRole('button', { name: 'Salir' });
    this.userEmail = page.locator('.ant-layout-header').locator('text=@');
  }

  async goto(): Promise<void> {
    await this.page.goto('/dashboard');
    await this.waitForDashboardReady();
  }

  async waitForDashboardReady(): Promise<void> {
    // Esperar que el heading sea visible (indica que React monto el componente)
    await expect(this.heading).toBeVisible({ timeout: 15000 });
    // Esperar que el spinner de carga desaparezca
    await expect(this.spinnerLoading).toBeHidden({ timeout: 10000 });
  }

  async getKpiValue(kpiLocator: Locator): Promise<string> {
    const valueEl = kpiLocator.locator('.ant-statistic-content-value');
    return (await valueEl.textContent()) || '';
  }

  async expectAllKpisVisible(): Promise<void> {
    await expect(this.kpiTotalAlumnos).toBeVisible();
    await expect(this.kpiTotalProfesores).toBeVisible();
    await expect(this.kpiIngresosMes).toBeVisible();
    await expect(this.kpiMorosidad).toBeVisible();
  }

  async expectChartRendered(): Promise<void> {
    // El canvas existe y tiene dimensiones > 0 cuando Chart.js renderizo correctamente
    await expect(this.ingresosMensualesChart).toBeVisible();
    const boundingBox = await this.ingresosMensualesChart.boundingBox();
    expect(boundingBox?.width).toBeGreaterThan(0);
    expect(boundingBox?.height).toBeGreaterThan(0);
  }

  async navigateTo(menuLabel: string): Promise<void> {
    await this.sidebarMenu.getByRole('menuitem', { name: menuLabel }).click();
  }

  async logout(): Promise<void> {
    await this.logoutButton.click();
    await expect(this.page).toHaveURL(/.*login/);
  }
}
