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
 * NOTAS DE SELECTORES:
 *   - El select "Ano" tiene valor por defecto (currentYear), no muestra placeholder.
 *     Se localiza por posicion: es el 2do .ant-select dentro del Space de filtros.
 *   - Los selects del modal se localizan via el .ant-form-item que contiene el label,
 *     no filtrando el .ant-select por .ant-form-item-label (que es sibling, no descendant).
 *   - El modal QR usa modal.info de Ant Design: el titulo aparece en .ant-modal-confirm-title.
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class PaymentsPage {
  readonly page: Page;

  readonly heading: Locator;
  readonly paymentsTable: Locator;
  readonly tableRows: Locator;
  // Filtros: los tres selects en el Space de filtros (por posicion/placeholder)
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

    // Los tres selects de filtro estan en un Space consecutivo antes de la tabla.
    // "Mes": el 1er .ant-select de la pagina
    this.mesFilterSelect = page.locator('.ant-select').nth(0);

    // "Ano": tiene valor por defecto (currentYear), NO muestra placeholder.
    // Se localiza como el 2do .ant-select de la pagina (Space: Mes[0], Ano[1], Estado[2]).
    this.anioFilterSelect = page.locator('.ant-select').nth(1);

    // "Estado": el 3er .ant-select de la pagina (puede tener valor o placeholder)
    this.estadoFilterSelect = page.locator('.ant-select').nth(2);

    // Modal de pago: localizamos via el Form.Item que contiene la label, luego el select dentro
    this.payModal = page.locator('.ant-modal', { hasText: 'Registrar Pago' });
    this.payModalTitle = this.payModal.locator('.ant-modal-title');
    this.montoInput = this.payModal.locator('.ant-input-number-input');
    this.fechaPagoInput = this.payModal.getByLabel('Fecha de Pago');
    // El Form.Item con label "Metodo de Pago" contiene el .ant-select
    this.metodoPagoSelect = this.payModal
      .locator('.ant-form-item', { has: page.locator('label', { hasText: 'Metodo de Pago' }) })
      .locator('.ant-select');
    this.observacionesInput = this.payModal.getByLabel('Observaciones');
    this.payModalOkButton = this.payModal.locator('.ant-modal-footer button.ant-btn-primary');

    // Modal de QR (creado por modal.info de Ant Design).
    // modal.info usa .ant-modal-confirm con titulo en .ant-modal-confirm-title
    this.qrModal = page.locator('.ant-modal-confirm', { hasText: 'QR de Pago' });
    this.qrImage = this.qrModal.locator('img[alt="QR Code"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/pensiones');
    await expect(this.heading).toBeVisible({ timeout: 10000 });
    // Esperar que los spinners desaparezcan (puede haber mas de uno)
    await expect(this.page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
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
    await expect(this.page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')).toHaveCount(0, { timeout: 5000 });
  }

  async filterByMes(mesLabel: string): Promise<void> {
    await this.selectAntOption(this.mesFilterSelect, mesLabel);
    await expect(this.page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
  }

  async filterByAnio(anio: number): Promise<void> {
    await this.selectAntOption(this.anioFilterSelect, String(anio));
    await expect(this.page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
  }

  async filterByEstado(estado: 'Pendiente' | 'Pagado' | 'Vencido'): Promise<void> {
    await this.selectAntOption(this.estadoFilterSelect, estado);
    await expect(this.page.locator('.ant-spin-spinning')).toHaveCount(0, { timeout: 10000 });
  }

  /**
   * Abre el modal de registrar pago para una fila de la tabla.
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
    // Ant Design con locale es_ES usa "Aceptar" en vez de "OK"
    await this.qrModal.getByRole('button', { name: /Aceptar|OK/ }).click();
    await expect(this.qrModal).toBeHidden();
  }

  async getRowEstado(rowIndex: number): Promise<string> {
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
