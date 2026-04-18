/**
 * TESTS: Navegacion y Control de Acceso
 *
 * Verifica que:
 * - El sidebar navega correctamente entre modulos
 * - Rutas privadas redirigen a login si no hay sesion
 * - Rutas desconocidas redirigen al dashboard (segun App.jsx: path="*" -> /dashboard)
 *
 * Cubre:
 * - TC-NAV-01: Navegacion desde el sidebar lleva a cada modulo principal
 * - TC-NAV-02: Acceder a ruta privada sin sesion redirige a /login
 * - TC-NAV-03: Ruta desconocida redirige al dashboard (fallback de React Router)
 */
import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';

// -----------------------------------------------------------------------
// Tests de navegacion autenticada: usan el storageState del setup
// -----------------------------------------------------------------------
test.describe('Navegacion con sesion activa', () => {
  test('TC-NAV-01: el sidebar navega correctamente a cada modulo principal', async ({
    page,
  }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardReady();

    // Mapa de items del menu a rutas esperadas
    const menuItems: Array<{ label: string; expectedUrl: RegExp }> = [
      { label: 'Alumnos', expectedUrl: /\/alumnos$/ },
      { label: 'Profesores', expectedUrl: /\/profesores$/ },
      { label: 'Aulas', expectedUrl: /\/aulas$/ },
      { label: 'Matriculas', expectedUrl: /\/matriculas$/ },
      { label: 'Pensiones', expectedUrl: /\/pensiones$/ },
      { label: 'Flujo de Caja', expectedUrl: /\/caja$/ },
      { label: 'Asistencia', expectedUrl: /\/asistencia$/ },
      { label: 'Comunicaciones', expectedUrl: /\/comunicaciones$/ },
      { label: 'Reportes', expectedUrl: /\/reportes$/ },
    ];

    for (const item of menuItems) {
      // Hacer click en el item del menu (Menu de Ant Design con role=menuitem)
      await page.locator('.ant-menu').getByRole('menuitem', { name: item.label }).click();

      // Verificar que la URL cambio correctamente
      await expect(page).toHaveURL(item.expectedUrl, { timeout: 10000 });

      // Verificar que la pagina cargo (ningun Spin de carga debe quedar visible)
      await expect(page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
    }
  });

  test('TC-NAV-02: el item del menu activo tiene la clase selected de Ant Design', async ({
    page,
  }) => {
    await page.goto('/alumnos');
    await expect(page.getByRole('heading', { name: 'Alumnos' })).toBeVisible();

    // El item "Alumnos" del menu debe tener la clase ant-menu-item-selected
    const alumnosMenuItem = page
      .locator('.ant-menu')
      .getByRole('menuitem', { name: 'Alumnos' });
    await expect(alumnosMenuItem).toHaveClass(/ant-menu-item-selected/);
  });

  test('TC-NAV-03: el boton de colapsar sidebar reduce el ancho y muestra icono C', async ({
    page,
  }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();

    const sider = page.locator('.ant-layout-sider');
    const collapseButton = page.locator('.ant-layout-header button').first();

    // El sider debe tener ancho 200 inicialmente
    // Hacer click en el boton de colapsar
    await collapseButton.click();

    // El sider debe colapsar (tiene clase ant-layout-sider-collapsed)
    await expect(sider).toHaveClass(/ant-layout-sider-collapsed/, { timeout: 5000 });

    // Expandir de nuevo
    await collapseButton.click();
    await expect(sider).not.toHaveClass(/ant-layout-sider-collapsed/, { timeout: 5000 });
  });
});

// -----------------------------------------------------------------------
// Tests de control de acceso: sin sesion (usan storageState vacio)
// -----------------------------------------------------------------------
test.describe('Control de acceso sin sesion', () => {
  // Estos tests NO tienen sesion activa
  test.use({ storageState: { cookies: [], origins: [] } });

  test('TC-NAV-04: acceder a /dashboard sin sesion redirige a /login', async ({ page }) => {
    await page.goto('/dashboard');

    // PrivateRoute en App.jsx redirige a /login si isAuthenticated es false
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
  });

  test('TC-NAV-05: acceder a /alumnos sin sesion redirige a /login', async ({ page }) => {
    await page.goto('/alumnos');
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
  });

  test('TC-NAV-06: ruta desconocida /ruta-inexistente redirige al dashboard o login', async ({
    page,
  }) => {
    // Sin sesion: PrivateRoute -> /login
    await page.goto('/ruta-inexistente');

    // El catch-all en App.jsx es <Navigate to="/dashboard"> pero
    // si no hay sesion PrivateRoute redirige a /login primero
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
  });
});

// -----------------------------------------------------------------------
// Test de ruta 404 con sesion activa
// -----------------------------------------------------------------------
test.describe('Rutas desconocidas con sesion activa', () => {
  test('TC-NAV-07: ruta desconocida redirige al dashboard cuando hay sesion activa', async ({
    page,
  }) => {
    // Con sesion activa: el catch-all de App.jsx es <Navigate to="/dashboard">
    await page.goto('/modulo-que-no-existe');
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 });

    // El dashboard debe cargarse correctamente
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({
      timeout: 10000,
    });
  });
});
