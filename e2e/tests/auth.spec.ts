/**
 * TESTS: Autenticacion
 *
 * Estos tests NO usan storageState porque prueban el flujo de login/logout en si.
 * Se ejecutan sin la sesion pre-autenticada del setup.
 *
 * Cubre:
 * - TC-AUTH-01: Login exitoso redirige al dashboard
 * - TC-AUTH-02: Credenciales invalidas muestra mensaje de error
 * - TC-AUTH-03: Logout limpia sesion y redirige a login
 */
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

// IMPORTANTE: estos tests ignoran el storageState del proyecto
// porque necesitan empezar sin sesion activa.
test.use({ storageState: { cookies: [], origins: [] } });

const TEST_EMAIL = process.env.TEST_EMAIL || 'admin@garabato.test';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'admin123';

test.describe('Autenticacion', () => {
  test('TC-AUTH-01: login exitoso redirige al dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Verificar que la pagina de login se renderizo correctamente
    await expect(loginPage.cardTitle).toBeVisible();
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();

    // Ejecutar login
    await loginPage.login(TEST_EMAIL, TEST_PASSWORD);

    // Debe redirigir al dashboard
    await loginPage.expectRedirectToDashboard();

    // El heading del dashboard debe ser visible
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({
      timeout: 10000,
    });

    // El email del usuario debe aparecer en el header
    await expect(page.locator('.ant-layout-header').getByText('@')).toBeVisible();
  });

  test('TC-AUTH-02: credenciales invalidas muestra mensaje de error de Ant Design', async ({
    page,
  }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('usuario@invalido.com', 'contrasenaMala123');

    // El mensaje de error de Ant Design (message.error) debe aparecer
    await loginPage.expectAntMessageError('Credenciales incorrectas');

    // Debe permanecer en la pagina de login
    await expect(page).toHaveURL(/.*login/);

    // El formulario debe seguir visible (no resetear)
    await expect(loginPage.emailInput).toBeVisible();
  });

  test('TC-AUTH-03: validacion de campos vacios muestra errores inline', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Intentar submit sin llenar campos
    await loginPage.submitButton.click();

    // Ant Design Form muestra errores inline bajo cada campo
    await loginPage.expectValidationError('Correo electronico', 'Ingrese su correo');
    await loginPage.expectValidationError('Contrasena', 'Ingrese su contrasena');

    // Debe permanecer en la pagina de login
    await expect(page).toHaveURL(/.*login/);
  });
});

// Este test SI necesita sesion activa para verificar logout
test.describe('Logout', () => {
  // Reusar el storageState del setup para este test
  test('TC-AUTH-04: logout limpia la sesion y redirige a /login', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardReady();

    // Ejecutar logout via el boton "Salir" del header
    await dashboardPage.logout();

    // Debe estar en la pagina de login
    await expect(page).toHaveURL(/.*login/);

    // Intentar navegar al dashboard directamente debe redirigir a login (PrivateRoute)
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);

    // El localStorage debe estar limpio (sin tokens)
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(accessToken).toBeNull();
  });
});
