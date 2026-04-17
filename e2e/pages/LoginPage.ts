/**
 * PAGE OBJECT: Login
 *
 * Componente: src/pages/Login.jsx
 * Ruta: /login
 *
 * Ant Design Form con name="login".
 * Los inputs NO tienen data-testid en el codigo actual.
 * Se usan getByLabel() que es semantico y robusto en Ant Design.
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="login-email-input"    en el Input de email
 *   - data-testid="login-password-input" en el Input.Password
 *   - data-testid="login-submit-btn"     en el Button de submit
 *   - data-testid="login-error-message"  en el mensaje de error (si se agrega)
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;

  // Locators: Ant Design Form.Item genera labels accesibles automaticamente
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly cardTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    // getByLabel busca el input asociado al label (Ant Design los vincula con htmlFor)
    this.emailInput = page.getByLabel('Correo electronico');
    // Input.Password de Ant Design: el label es "Contrasena"
    this.passwordInput = page.getByLabel('Contrasena');
    // El boton de submit usa role=button con su texto visible
    this.submitButton = page.getByRole('button', { name: 'Iniciar Sesion' });
    this.cardTitle = page.getByRole('heading', { name: 'SAAS COREM' });
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
    // Esperar que el card de login este visible antes de interactuar
    await expect(this.cardTitle).toBeVisible();
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectRedirectToDashboard(): Promise<void> {
    await expect(this.page).toHaveURL(/.*dashboard/, { timeout: 10000 });
  }

  async expectValidationError(fieldLabel: string, errorMessage: string): Promise<void> {
    // Ant Design muestra errores de validacion debajo del campo con clase ant-form-item-explain-error
    const formItem = this.page.locator('.ant-form-item', { hasText: fieldLabel });
    await expect(formItem.locator('.ant-form-item-explain-error')).toContainText(errorMessage);
  }

  async expectLoginButtonLoading(): Promise<void> {
    // Ant Design agrega la clase ant-btn-loading cuando loading=true
    await expect(this.submitButton).toHaveClass(/ant-btn-loading/);
  }

  async expectAntMessageError(text: string): Promise<void> {
    // Los mensajes globales de Ant Design (message.error) aparecen en .ant-message-notice
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: text })
    ).toBeVisible({ timeout: 5000 });
  }
}
