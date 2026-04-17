/**
 * PAGE OBJECT: Pensiones (Payments)
 *
 * Componente: src/pages/Payments.jsx
 * Ruta: /pensiones
 *
 * Tabla de pagos con filtros por mes, ano y estado.
 * Modal para registrar pago (monto, fecha, metodo, observaciones).
 * Boton QR que abre modal con imagen.
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="payments-table"           en el Table
 *   - data-testid="select-mes-filtro"        en el Select de mes
 *   - data-testid="select-anio-filtro"       en el Select de ano
 *   - data-testid="select-estado-filtro"     en el Select de estado
 *   - data-testid="modal-registrar-pago"     en el Modal de pago
 *   - data-testid="modal-qr"                 en el Modal del QR
 *   - data-testid="qr-image"                 en la img del QR
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class PaymentsPage {
  readonly page: Page;

  readonly heading: Locator;
  readonly paymentsTable: Locator;
  readonly tableRows: Locator;
  // Filtros: cada Select se identifica por su placeholder visible
  readonly mesFilterSelect: Locator;
  readonly anioFilterSelect: Locator;
  readonly estadoFilterSelect: Locator;
  // Modal de registrar pago
  readonly payModal: Locator;
  readonly payModalTitle: Locator;
  readonly montoInput: Locator;
  readonly fechaPagoInput: Locator;
  readonly metodoPagoSelect: Locator;
  readonly observacionesInput: Locator;
  readonly payModalOkButton: Locator;
  // Modal de QR
  readonly qrModal: Locator;
  readonly qrImage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Pensiones' });
    this.paymentsTable = page.locator('.ant-table-wrapper');
    this.tableRows = page.locator('.ant-table-tbody tr.ant-table-row');

    // Los Select de filtro: Ant Design coloca el placeholder en .ant-select-selection-placeholder
    this.mesFilterSelect = page
      .locator('.ant-select')
      .filter({ has: page.locator('.ant-select-selection-placeholder', { hasText: 'Mes' }) });
    this.anioFilterSelect = page
      .locator('.ant-select')
      .filter({ has: page.locator('.ant-select-selection-placeholder', { hasText: 'Ano' }) });
    this.estadoFilterSelect = page
      .locator('.ant-select')
      .filter({ has: page.locator('.ant-select-selection-placeholder', { hasText: 'Estado' }) });

    // Modal de pago
    this.payModal = page.locator('.ant-modal', { hasText: 'Registrar Pago' });
    this.payModalTitle = this.payModal.locator('.ant-modal-title');
    this.montoInput = this.payModal.locator('.ant-input-number-input');
    this.fechaPagoInput = this.payModal.getByLabel('Fecha de Pago');
    this.metodoPagoSelect = this.payModal
      .locator('.ant-select')
      .filter({ has: this.payModal.locator('.ant-form-item-label', { hasText: 'Metodo' }) });
    this.observacionesInput = this.payModal.getByLabel('Observaciones');
    this.payModalOkButton = this.payModal.locator('.ant-modal-footer button.ant-btn-primary');

    // Modal de QR (creado por modal.info de Ant Design)
    this.qrModal = page.locator('.ant-modal', { hasText: 'QR de Pago' });
    this.qrImage = this.qrModal.locator('img[alt="QR Code"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/pensiones');
    await expect(this.heading).toBeVisible({ timeout: 10000 });
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  /**
   * Selecciona una opcion en un Select de Ant Design.
   */
  private async selectAntOption(selectLocator: Locator, optionText: string): Promise<void> {
    await selectLocator.click();
    await this.page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .getByTitle(optionText)
      .click();
    await expect(this.page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')).toBeHidden();
  }

  async filterByMes(mesLabel: string): Promise<void> {
    await this.selectAntOption(this.mesFilterSelect, mesLabel);
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  async filterByAnio(anio: number): Promise<void> {
    await this.selectAntOption(this.anioFilterSelect, String(anio));
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  async filterByEstado(estado: 'Pendiente' | 'Pagado' | 'Vencido'): Promise<void> {
    await this.selectAntOption(this.estadoFilterSelect, estado);
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  /**
   * Abre el modal de registrar pago para la primera fila con estado PENDIENTE.
   * El boton "Registrar Pago" solo aparece si el estado no es PAGADO.
   */
  async clickRegistrarPago(rowIndex: number = 0): Promise<void> {
    await this.tableRows.nth(rowIndex).getByRole('button', { name: 'Registrar Pago' }).click();
    await expect(this.payModal).toBeVisible();
  }

  async fillPaymentForm(data: {
    monto?: number;
    fechaPago?: string;
    metodoPago?: 'Efectivo' | 'Transferencia' | 'Yape' | 'Plin';
    observaciones?: string;
  }): Promise<void> {
    if (data.monto !== undefined) {
      await this.montoInput.triple_click?.();
      await this.montoInput.fill(String(data.monto));
    }
    if (data.fechaPago !== undefined) {
      await this.fechaPagoInput.click();
      await this.fechaPagoInput.fill(data.fechaPago);
      await this.fechaPagoInput.press('Enter');
    }
    if (data.metodoPago !== undefined) {
      await this.selectAntOption(this.metodoPagoSelect, data.metodoPago);
    }
    if (data.observaciones !== undefined) {
      await this.observacionesInput.fill(data.observaciones);
    }
  }

  async submitPayment(): Promise<void> {
    await this.payModalOkButton.click();
    await expect(this.payModal).toBeHidden({ timeout: 10000 });
  }

  async clickGenerarQR(rowIndex: number = 0): Promise<void> {
    await this.tableRows.nth(rowIndex).getByRole('button', { name: 'QR' }).click();
  }

  async closeQrModal(): Promise<void> {
    await this.qrModal.getByRole('button', { name: 'OK' }).click();
    await expect(this.qrModal).toBeHidden();
  }

  async getRowEstado(rowIndex: number): Promise<string> {
    // La columna Estado tiene un Tag de Ant Design
    return (
      (await this.tableRows.nth(rowIndex).locator('.ant-tag').textContent()) || ''
    );
  }

  async expectSuccessMessage(text: string): Promise<void> {
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: text })
    ).toBeVisible({ timeout: 5000 });
  }
}
