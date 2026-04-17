/**
 * PAGE OBJECT: Detalle de Alumno
 *
 * Componente: src/pages/StudentDetail.jsx
 * Ruta: /alumnos/:id
 *
 * Descriptions con datos del alumno.
 * Tabs: Apoderados (tabla) | Ficha Medica (form) | Historial (tabla).
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="student-detail-card"    en el Card de descripcion
 *   - data-testid="btn-volver-alumnos"     en el Button "Volver"
 *   - data-testid="tab-apoderados"         en la Tab de Apoderados
 *   - data-testid="tab-ficha-medica"       en la Tab de Ficha Medica
 *   - data-testid="btn-guardar-ficha"      en el Button "Guardar Ficha Medica"
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class StudentDetailPage {
  readonly page: Page;

  readonly backButton: Locator;
  readonly spinnerLoading: Locator;
  readonly studentDescriptions: Locator;
  // Tabs
  readonly tabsContainer: Locator;
  readonly tabApoderados: Locator;
  readonly tabFichaMedica: Locator;
  readonly tabHistorial: Locator;
  // Tab Ficha Medica - campos del formulario
  readonly alergiasTextarea: Locator;
  readonly condicionesMedicasTextarea: Locator;
  readonly medicamentosTextarea: Locator;
  readonly tipoSangreInput: Locator;
  readonly contactoEmergenciaInput: Locator;
  readonly telefonoEmergenciaInput: Locator;
  readonly observacionesFichaTextarea: Locator;
  readonly saveFichaButton: Locator;
  // Tab Apoderados - tabla
  readonly apoderadosTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.backButton = page.getByRole('button', { name: 'Volver' });
    this.spinnerLoading = page.locator('.ant-spin-spinning');
    // Las Descriptions de Ant Design
    this.studentDescriptions = page.locator('.ant-descriptions');
    this.tabsContainer = page.locator('.ant-tabs');
    // Los tabs se identifican por su texto dentro de .ant-tabs-tab
    this.tabApoderados = page.locator('.ant-tabs-tab', { hasText: 'Apoderados' });
    this.tabFichaMedica = page.locator('.ant-tabs-tab', { hasText: 'Ficha Medica' });
    this.tabHistorial = page.locator('.ant-tabs-tab', { hasText: 'Historial' });

    // Campos del formulario de ficha medica (getByLabel funciona con Form.Item label)
    this.alergiasTextarea = page.getByLabel('Alergias');
    this.condicionesMedicasTextarea = page.getByLabel('Condiciones Medicas');
    this.medicamentosTextarea = page.getByLabel('Medicamentos');
    this.tipoSangreInput = page.getByLabel('Tipo de Sangre');
    this.contactoEmergenciaInput = page.getByLabel('Contacto de Emergencia');
    this.telefonoEmergenciaInput = page.getByLabel('Telefono Emergencia');
    this.observacionesFichaTextarea = page.locator('form').getByLabel('Observaciones');
    this.saveFichaButton = page.getByRole('button', { name: 'Guardar Ficha Medica' });

    this.apoderadosTable = page.locator('.ant-table-wrapper');
  }

  async gotoById(id: number): Promise<void> {
    await this.page.goto(`/alumnos/${id}`);
    await this.waitForReady();
  }

  async waitForReady(): Promise<void> {
    await expect(this.spinnerLoading).toBeHidden({ timeout: 15000 });
    await expect(this.studentDescriptions).toBeVisible();
  }

  async getStudentName(): Promise<string> {
    // El titulo del heading tiene el nombre completo del alumno
    const heading = this.page.getByRole('heading', { level: 4 });
    return (await heading.textContent()) || '';
  }

  async getDescriptionValue(label: string): Promise<string> {
    const item = this.studentDescriptions.locator('.ant-descriptions-item', { hasText: label });
    return (await item.locator('.ant-descriptions-item-content').textContent()) || '';
  }

  async clickTabApoderados(): Promise<void> {
    await this.tabApoderados.click();
    // Esperar que el panel del tab sea visible
    await expect(this.apoderadosTable).toBeVisible();
  }

  async clickTabFichaMedica(): Promise<void> {
    await this.tabFichaMedica.click();
    await expect(this.saveFichaButton).toBeVisible();
  }

  async fillFichaMedica(data: {
    alergias?: string;
    condicionesMedicas?: string;
    tipoSangre?: string;
    contactoEmergencia?: string;
    telefonoEmergencia?: string;
  }): Promise<void> {
    if (data.alergias !== undefined) {
      await this.alergiasTextarea.fill(data.alergias);
    }
    if (data.condicionesMedicas !== undefined) {
      await this.condicionesMedicasTextarea.fill(data.condicionesMedicas);
    }
    if (data.tipoSangre !== undefined) {
      await this.tipoSangreInput.fill(data.tipoSangre);
    }
    if (data.contactoEmergencia !== undefined) {
      await this.contactoEmergenciaInput.fill(data.contactoEmergencia);
    }
    if (data.telefonoEmergencia !== undefined) {
      await this.telefonoEmergenciaInput.fill(data.telefonoEmergencia);
    }
  }

  async saveFichaMedica(): Promise<void> {
    await this.saveFichaButton.click();
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: 'Ficha medica guardada' })
    ).toBeVisible({ timeout: 5000 });
  }

  async goBack(): Promise<void> {
    await this.backButton.click();
    await expect(this.page).toHaveURL(/.*\/alumnos$/);
  }
}
