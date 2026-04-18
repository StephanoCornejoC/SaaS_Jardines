/**
 * PAGE OBJECT: Caja (Cashflow)
 *
 * Componente: src/pages/Cashflow.jsx
 * Ruta: /caja
 *
 * Cards de resumen (Ingresos, Egresos, Balance).
 * Tabs: Transacciones | Cierres Mensuales.
 * Modal para nueva transaccion.
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="stat-ingresos"           en el Statistic de Ingresos
 *   - data-testid="stat-egresos"            en el Statistic de Egresos
 *   - data-testid="stat-balance"            en el Statistic de Balance
 *   - data-testid="btn-nueva-transaccion"   en el Button "Nueva Transaccion"
 *   - data-testid="tab-transacciones"       en la Tab de Transacciones
 *   - data-testid="tab-cierres"             en la Tab de Cierres Mensuales
 *   - data-testid="modal-transaccion"       en el Modal
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class CashflowPage {
  readonly page: Page;

  readonly heading: Locator;
  readonly newTransactionButton: Locator;
  // Cards de resumen (Statistic de Ant Design)
  readonly statIngresos: Locator;
  readonly statEgresos: Locator;
  readonly statBalance: Locator;
  // Tabs
  readonly tabTransacciones: Locator;
  readonly tabCierres: Locator;
  // Tabla de transacciones
  readonly transactionsTable: Locator;
  readonly transactionRows: Locator;
  // Tabla de cierres mensuales
  readonly closuresTable: Locator;
  // Modal de nueva transaccion
  readonly modal: Locator;
  readonly tipoSelect: Locator;
  readonly categoriaSelect: Locator;
  readonly descripcionTextarea: Locator;
  readonly montoInput: Locator;
  readonly fechaInput: Locator;
  readonly modalOkButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Caja' });
    this.newTransactionButton = page.getByRole('button', { name: 'Nueva Transaccion' });

    // Los Statistic se identifican por su titulo
    this.statIngresos = page.locator('.ant-statistic', { hasText: 'Ingresos del Mes' });
    this.statEgresos = page.locator('.ant-statistic', { hasText: 'Egresos del Mes' });
    this.statBalance = page.locator('.ant-statistic', { hasText: 'Balance' });

    this.tabTransacciones = page.locator('.ant-tabs-tab', { hasText: 'Transacciones' });
    this.tabCierres = page.locator('.ant-tabs-tab', { hasText: 'Cierres Mensuales' });

    // Las tablas estan dentro de paneles del Tabs
    // El primer .ant-table-wrapper dentro del panel activo
    this.transactionsTable = page.locator('.ant-tabs-tabpane-active .ant-table-wrapper');
    this.transactionRows = page.locator('.ant-tabs-tabpane-active .ant-table-tbody tr.ant-table-row');

    this.closuresTable = page.locator('.ant-tabs-tabpane-active .ant-table-wrapper');

    // Modal de nueva transaccion
    this.modal = page.locator('.ant-modal', { hasText: 'Nueva Transaccion' });
    // Los Select del modal se localizan usando getByRole('combobox') con el aria-label del campo.
    // Ant Design 5 Form.Item con label "Tipo" genera un combobox con aria-label "* Tipo".
    // Clickeamos el .ant-select-selector (elemento clickable) que es padre del combobox.
    // Usamos nth(0) para Tipo y nth(1) para Categoria, que son los primeros dos selects del modal.
    this.tipoSelect = this.modal.locator('.ant-select').nth(0);
    this.categoriaSelect = this.modal.locator('.ant-select').nth(1);
    this.descripcionTextarea = this.modal.getByLabel('Descripcion');
    this.montoInput = this.modal.locator('.ant-input-number-input');
    this.fechaInput = this.modal.locator('.ant-picker input');
    this.modalOkButton = this.modal.locator('.ant-modal-footer button.ant-btn-primary');
  }

  async goto(): Promise<void> {
    await this.page.goto('/caja');
    await expect(this.heading).toBeVisible({ timeout: 10000 });
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  private async selectAntOption(selectLocator: Locator, optionText: string): Promise<void> {
    await selectLocator.click();
    await this.page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .getByTitle(optionText)
      .click();
  }

  async openNewTransactionModal(): Promise<void> {
    await this.newTransactionButton.click();
    await expect(this.modal).toBeVisible();
  }

  async fillTransactionForm(data: {
    tipo: 'Ingreso' | 'Egreso';
    categoria: string;
    descripcion: string;
    monto: number;
    fecha: string;
  }): Promise<void> {
    await this.selectAntOption(this.tipoSelect, data.tipo);
    await this.selectAntOption(this.categoriaSelect, data.categoria);
    await this.descripcionTextarea.fill(data.descripcion);
    await this.montoInput.fill(String(data.monto));
    await this.fechaInput.click();
    await this.fechaInput.fill(data.fecha);
    await this.fechaInput.press('Enter');
  }

  async submitTransaction(): Promise<void> {
    await this.modalOkButton.click();
    await expect(this.modal).toBeHidden({ timeout: 10000 });
  }

  async clickTabCierres(): Promise<void> {
    await this.tabCierres.click();
    // Esperar que el panel de cierres sea el activo
    await expect(this.page.locator('.ant-tabs-tabpane-active')).toBeVisible();
  }

  async clickTabTransacciones(): Promise<void> {
    await this.tabTransacciones.click();
  }

  async getStatValue(statLocator: Locator): Promise<number> {
    const text = (await statLocator.locator('.ant-statistic-content-value').textContent()) || '0';
    return parseFloat(text.replace(/,/g, ''));
  }

  async getTransactionCount(): Promise<number> {
    // Wait for any data loading spinner to disappear before counting
    await expect(this.page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
    // Small stabilization wait for the table to render its current rows
    await this.page.waitForTimeout(300);
    return await this.transactionRows.count();
  }

  async expectTransactionInTable(descripcion: string): Promise<void> {
    await expect(
      this.transactionsTable.locator('td', { hasText: descripcion })
    ).toBeVisible();
  }

  async expectSuccessMessage(text: string): Promise<void> {
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: text })
    ).toBeVisible({ timeout: 5000 });
  }

  async expectModalValidationError(fieldLabel: string): Promise<void> {
    const formItem = this.modal.locator('.ant-form-item', { hasText: fieldLabel });
    await expect(formItem.locator('.ant-form-item-explain-error')).toBeVisible();
  }
}
