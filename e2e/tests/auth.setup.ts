/**
 * AUTH SETUP - Ejecuta una sola vez antes de todos los proyectos de browser.
 *
 * Hace login via API (mas rapido que via UI) y guarda el storage state
 * con los tokens JWT en localStorage. Todos los proyectos reutilizan
 * esta sesion para no repetir login en cada test.
 *
 * NOTA: Si el backend cambia la URL de token (/auth/token/) actualizar aqui.
 */
import { test as setup, expect } from '@playwright/test';

const AUTH_FILE = 'playwright/.auth/user.json';
const API_URL = process.env.API_URL || 'http://localhost:8000';
const TEST_EMAIL = process.env.TEST_EMAIL || 'admin@garabato.test';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'admin123';

setup('autenticar usuario de prueba', async ({ page, request }) => {
  // 0. Cleanup previos: borrar alumnos creados por tests anteriores (DNIs > 71000005 son de seed)
  const loginForCleanup = await request.post(`${API_URL}/api/v1/auth/token/`, {
    data: { email: TEST_EMAIL, password: TEST_PASSWORD },
  });
  if (loginForCleanup.ok()) {
    const { access: cleanupToken } = await loginForCleanup.json();
    const studentsRes = await request.get(`${API_URL}/api/v1/students/?page_size=200`, {
      headers: { Authorization: `Bearer ${cleanupToken}` },
    });
    if (studentsRes.ok()) {
      const students = await studentsRes.json();
      const list = students.results || students;
      for (const s of list) {
        // DNIs de seed: 71000001-71000005, cualquier otro es test-creado y se elimina
        if (!s.dni?.startsWith('71000')) {
          await request.delete(`${API_URL}/api/v1/students/${s.id}/`, {
            headers: { Authorization: `Bearer ${cleanupToken}` },
          });
        }
      }
    }
  }

  // 1. Obtener JWT via API (evita pasar por la UI de login en cada suite)
  const tokenResponse = await request.post(`${API_URL}/api/v1/auth/token/`, {
    data: { email: TEST_EMAIL, password: TEST_PASSWORD },
    headers: { 'Content-Type': 'application/json' },
  });

  expect(tokenResponse.ok(), `Login via API fallo: ${await tokenResponse.text()}`).toBeTruthy();

  const { access, refresh } = await tokenResponse.json();
  expect(access).toBeTruthy();

  // 2. Obtener datos del usuario para el store de Zustand
  const meResponse = await request.get(`${API_URL}/api/v1/auth/users/me/`, {
    headers: { Authorization: `Bearer ${access}` },
  });

  expect(meResponse.ok()).toBeTruthy();
  const userData = await meResponse.json();

  // 3. Navegar al frontend e inyectar tokens en localStorage
  //    Esto replica exactamente lo que hace authStore.js
  await page.goto('/login');

  await page.evaluate(
    ({ accessToken, refreshToken, user }) => {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
    },
    { accessToken: access, refreshToken: refresh, user: userData }
  );

  // 4. Verificar que la sesion funciona navegando al dashboard
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/.*dashboard/);
  // El titulo del dashboard siempre esta visible cuando hay sesion valida
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  // 5. Guardar el storage state (localStorage + cookies) para reutilizar
  await page.context().storageState({ path: AUTH_FILE });
});
