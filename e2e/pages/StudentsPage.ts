/**
 * PAGE OBJECT: Alumnos
 *
 * Componente: src/pages/Students.jsx
 * Ruta: /alumnos
 *
 * Tabla Ant Design con CRUD completo.
 * Modal de creacion/edicion con Form.
 * Botones de accion en cada fila: Ver (link), Editar (link), Eliminar (danger link).
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="students-table"         en el componente Table
 *   - data-testid="btn-nuevo-alumno"       en el Button "Nuevo Alumno"
 *   - data-testid="input-buscar-alumno"    en el Input de busqueda
 *   - data-testid="select-estado-filtro"   en el Select de estado
 *   - data-testid="modal-alumno"           en el Modal de creacion/edicion
 *   - data-testid="btn-guardar-alumno"     en el boton OK del modal
 *
 * NOTA sobre Popconfirm de eliminacion:
 *   El componente Students.jsx usa api.delete directamente sin Popconfirm.
 *   Si se agrega confirmacion, el selector del boton "Eliminar" puede cambiar.
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class StudentsPage {
  readonly page: Page;

  readonly heading: Locator;
  readonly newStudentButton: Locator;
  readonly searchInput: Locator;
  readonly estadoFilterSelect: Locator;
  readonly studentsTable: Locator;
  readonly tableRows: Locator;
  // Modal de creacion/edicion
  readonly modal: Locator;
  readonly modalTitle: Locator;
  readonly modalOkButton: Locator;
  readonly modalCancelButton: Locator;
  // Campos del formulario dentro del modal
  readonly dniInput: Locator;
  readonly nombresInput: Locator;
  readonly apellidosInput: Locator;
  readonly fechaNacimientoInput: Locator;
  readonly generoSelect: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Alumnos' });
    this.newStudentButton = page.getByRole('button', { name: 'Nuevo Alumno' });

    // El Input con placeholder "Buscar por nombre o DNI"
    this.searchInput = page.getByPlaceholder('Buscar por nombre o DNI');

    // El Select de estado: buscar el trigger por placeholder "Estado"
    this.estadoFilterSelect = page.locator('.ant-select:has(.ant-select-selection-placeholder:has-text("Estado"))').first();

    this.studentsTable = page.locator('.ant-table-wrapper');
    this.tableRows = page.locator('.ant-table-tbody tr.ant-table-row');

    // Modal: Ant Design usa role=dialog
    this.modal = page.locator('.ant-modal');
    this.modalTitle = this.modal.locator('.ant-modal-title');
    // Los botones del footer del modal
    this.modalOkButton = this.modal.locator('.ant-modal-footer button.ant-btn-primary');
    this.modalCancelButton = this.modal.locator('.ant-modal-footer button:not(.ant-btn-primary)');

    // Campos dentro del modal (Form.Item con label)
    this.dniInput = this.modal.getByLabel('DNI');
    this.nombresInput = this.modal.getByLabel('Nombres');
    this.apellidosInput = this.modal.getByLabel('Apellidos');
    this.fechaNacimientoInput = this.modal.getByLabel('Fecha de Nacimiento');
    // El Select de Genero: buscar por el Form.Item con label "Genero" y dentro el select
    this.generoSelect = this.modal
      .locator('.ant-form-item')
      .filter({ has: page.locator('label', { hasText: 'Genero' }) })
      .locator('.ant-select');
  }

  async goto(): Promise<void> {
    await this.page.goto('/alumnos');
    await this.waitForTableReady();
  }

  async waitForTableReady(): Promise<void> {
    await expect(this.heading).toBeVisible({ timeout: 10000 });
    // Esperar que el spinner de la tabla desaparezca
    await expect(this.page.locator('.ant-spin-spinning')).toBeHidden({ timeout: 10000 });
  }

  async openCreateModal(): Promise<void> {
    await this.newStudentButton.click();
    await expect(this.modal).toBeVisible();
    await expect(this.modalTitle).toHaveText('Nuevo Alumno');
  }

  async openEditModal(rowIndex: number = 0): Promise<void> {
    await this.tableRows.nth(rowIndex).getByRole('button', { name: 'Editar' }).click();
    await expect(this.modal).toBeVisible();
    await expect(this.modalTitle).toHaveText('Editar Alumno');
  }

  async fillStudentForm(data: {
    dni?: string;
    nombres?: string;
    apellidos?: string;
    fechaNacimiento?: string;
    genero?: 'Masculino' | 'Femenino';
  }): Promise<void> {
    if (data.dni !== undefined) {
      await this.dniInput.clear();
      await this.dniInput.fill(data.dni);
    }
    if (data.nombres !== undefined) {
      await this.nombresInput.clear();
      await this.nombresInput.fill(data.nombres);
    }
    if (data.apellidos !== undefined) {
      await this.apellidosInput.clear();
      await this.apellidosInput.fill(data.apellidos);
    }
    if (data.fechaNacimiento !== undefined) {
      // Ant Design DatePicker: click para abrir el picker, luego escribir la fecha
      await this.fechaNacimientoInput.click();
      await this.fechaNacimientoInput.fill(data.fechaNacimiento);
      // Presionar Enter para confirmar la fecha
      await this.fechaNacimientoInput.press('Enter');
    }
    if (data.genero !== undefined) {
      await this.selectAntOption(this.generoSelect, data.genero);
    }
  }

  /**
   * Selecciona una opcion en un Select de Ant Design.
   * Ant Design Select usa un dropdown virtual, no un <select> nativo.
   */
  async selectAntOption(selectLocator: Locator, optionText: string): Promise<void> {
    await selectLocator.click();
    // Las opciones del dropdown se renderizan en el body (portal)
    await this.page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .getByTitle(optionText)
      .click();
  }

  async submitModal(): Promise<void> {
    await this.modalOkButton.click();
    // Esperar que el modal se cierre
    await expect(this.modal).toBeHidden({ timeout: 10000 });
  }

  async cancelModal(): Promise<void> {
    await this.modalCancelButton.click();
    await expect(this.modal).toBeHidden();
  }

  async searchStudent(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
    await this.waitForTableReady();
  }

  async filterByEstado(estado: 'Activo' | 'Retirado' | 'Egresado'): Promise<void> {
    await this.selectAntOption(this.estadoFilterSelect, estado);
    await this.waitForTableReady();
  }

  async clickViewStudent(rowIndex: number = 0): Promise<void> {
    // El icono EyeOutlined no tiene texto, buscar por el icono dentro del boton
    await this.tableRows.nth(rowIndex).locator('.anticon-eye').click();
  }

  async deleteStudent(rowIndex: number = 0): Promise<void> {
    await this.tableRows.nth(rowIndex).getByRole('button', { name: 'Eliminar' }).click();
    // Confirmar el Popconfirm de Ant Design
    await this.page
      .locator('.ant-popconfirm')
      .getByRole('button', { name: /Si, eliminar/i })
      .click();
  }

  async getRowCount(): Promise<number> {
    await this.waitForTableReady();
    return await this.tableRows.count();
  }

  async expectSuccessMessage(text: string): Promise<void> {
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: text })
    ).toBeVisible({ timeout: 5000 });
  }

  async expectModalValidationError(fieldLabel: string, errorText: string): Promise<void> {
    const formItem = this.modal.locator('.ant-form-item', { hasText: fieldLabel });
    await expect(formItem.locator('.ant-form-item-explain-error')).toContainText(errorText);
  }

  async getColumnValueInRow(rowIndex: number, columnIndex: number): Promise<string> {
    return (
      (await this.tableRows.nth(rowIndex).locator('td').nth(columnIndex).textContent()) || ''
    );
  }
}
