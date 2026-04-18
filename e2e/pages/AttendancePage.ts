/**
 * PAGE OBJECT: Asistencia
 *
 * Componente: src/pages/Attendance.jsx
 * Ruta: /asistencia
 *
 * Card de filtros: Select de aula + DatePicker de fecha.
 * Tabla de alumnos con Select de estado por fila (PRESENTE/AUSENTE/TARDANZA/JUSTIFICADO).
 * Boton "Guardar Asistencia" que llama a /attendance/registro-masivo/.
 *
 * DATA-TESTID PENDIENTES DE AGREGAR AL FRONTEND:
 *   - data-testid="select-aula-asistencia"   en el Select de aula
 *   - data-testid="datepicker-fecha-asist"   en el DatePicker
 *   - data-testid="btn-guardar-asistencia"   en el Button guardar
 *   - data-testid="attendance-table"         en el Table de alumnos
 */
import { type Locator, type Page, expect } from '@playwright/test';

export class AttendancePage {
  readonly page: Page;

  readonly heading: Locator;
  readonly aulaSelect: Locator;
  readonly fechaDatePicker: Locator;
  readonly saveButton: Locator;
  readonly attendanceTable: Locator;
  readonly tableRows: Locator;
  readonly spinnerLoading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Asistencia' });

    // El Card de filtros contiene los controles de seleccion
    // El Select de aula tiene placeholder "Seleccione aula"
    this.aulaSelect = page.locator('.ant-select').filter({
      has: page.locator('.ant-select-selection-placeholder', { hasText: 'Seleccione aula' }),
    });

    // El DatePicker de fecha (solo hay uno en la pagina)
    this.fechaDatePicker = page.locator('.ant-picker input').first();

    this.saveButton = page.getByRole('button', { name: 'Guardar Asistencia' });
    this.attendanceTable = page.locator('.ant-table-wrapper');
    this.tableRows = page.locator('.ant-table-tbody tr.ant-table-row');
    this.spinnerLoading = page.locator('.ant-spin-spinning');
  }

  async goto(): Promise<void> {
    await this.page.goto('/asistencia');
    await expect(this.heading).toBeVisible({ timeout: 10000 });
  }

  /**
   * Selecciona un aula del dropdown.
   * Las opciones muestran: "Nombre Aula (nivel)"
   */
  async selectAula(aulaDisplayText: string): Promise<void> {
    await this.aulaSelect.click();
    await this.page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .getByTitle(aulaDisplayText)
      .click();
    // Esperar que los alumnos del aula carguen
    await expect(this.spinnerLoading).toBeHidden({ timeout: 10000 });
  }

  /**
   * Establece la fecha en el DatePicker.
   * @param date Fecha en formato DD/MM/YYYY (como muestra el frontend)
   */
  async setFecha(date: string): Promise<void> {
    await this.fechaDatePicker.click();
    await this.fechaDatePicker.fill(date);
    await this.fechaDatePicker.press('Enter');
    // Esperar recarga de asistencia
    await expect(this.spinnerLoading).toBeHidden({ timeout: 10000 });
  }

  /**
   * Cambia el estado de asistencia de un alumno en la tabla.
   * @param rowIndex indice de la fila (0-based)
   * @param estado   PRESENTE | AUSENTE | TARDANZA | JUSTIFICADO
   */
  async setEstadoAlumno(
    rowIndex: number,
    estado: 'PRESENTE' | 'AUSENTE' | 'TARDANZA' | 'JUSTIFICADO'
  ): Promise<void> {
    const estadoLabels: Record<string, string> = {
      PRESENTE: 'Presente',
      AUSENTE: 'Ausente',
      TARDANZA: 'Tardanza',
      JUSTIFICADO: 'Justificado',
    };
    const row = this.tableRows.nth(rowIndex);
    const rowSelect = row.locator('.ant-select');

    // Cerrar cualquier dropdown abierto antes de abrir el nuevo
    // (evita strict mode violation cuando hay multiples dropdowns visibles)
    await expect(this.page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')).toHaveCount(0, { timeout: 3000 }).catch(() => {
      // Si hay un dropdown abierto, hacer Escape para cerrarlo
    });

    await rowSelect.click();

    // Esperar a que SOLO haya un dropdown visible (el de esta fila)
    await expect(
      this.page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
    ).toHaveCount(1, { timeout: 5000 });

    // Seleccionar la opcion usando .first() por seguridad
    await this.page
      .locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
      .first()
      .getByTitle(estadoLabels[estado])
      .click();

    // Esperar a que el dropdown se cierre
    await expect(
      this.page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)')
    ).toHaveCount(0, { timeout: 3000 });
  }

  /**
   * Marca todos los alumnos visibles con el mismo estado.
   */
  async markAllAs(estado: 'PRESENTE' | 'AUSENTE' | 'TARDANZA' | 'JUSTIFICADO'): Promise<void> {
    const count = await this.tableRows.count();
    for (let i = 0; i < count; i++) {
      await this.setEstadoAlumno(i, estado);
    }
  }

  async saveAttendance(): Promise<void> {
    await this.saveButton.click();
    await expect(
      this.page.locator('.ant-message-notice-content', { hasText: 'Asistencia guardada' })
    ).toBeVisible({ timeout: 8000 });
  }

  async expectSaveButtonDisabled(): Promise<void> {
    await expect(this.saveButton).toBeDisabled();
  }

  async getStudentCount(): Promise<number> {
    return await this.tableRows.count();
  }

  async getEstadoInRow(rowIndex: number): Promise<string> {
    const row = this.tableRows.nth(rowIndex);
    // El valor seleccionado del Select aparece en .ant-select-selection-item
    return (await row.locator('.ant-select-selection-item').textContent()) || '';
  }

  async expectEmptyTableMessage(): Promise<void> {
    await expect(
      this.attendanceTable.locator('.ant-table-placeholder', {
        hasText: 'Seleccione un aula para ver los alumnos',
      })
    ).toBeVisible();
  }
}
