/**
 * TESTS: Asistencia
 *
 * Prerequisito: sesion activa. Requiere que existan aulas activas con alumnos.
 *
 * Cubre:
 * - TC-ATT-01: Sin seleccion de aula la tabla muestra mensaje de guia
 * - TC-ATT-02: Seleccionar aula carga los alumnos del aula en la tabla
 * - TC-ATT-03: Guardar asistencia con todos PRESENTE envia registro masivo
 */
import { test, expect } from '../fixtures/auth';

test.describe('Asistencia', () => {
  test('TC-ATT-01: sin seleccion de aula la tabla muestra el mensaje de guia', async ({
    attendancePage,
  }) => {
    await attendancePage.goto();

    // El heading debe ser visible
    await expect(attendancePage.heading).toBeVisible();

    // El card de filtros debe mostrar el Select de aula y el DatePicker
    await expect(attendancePage.aulaSelect).toBeVisible();
    await expect(attendancePage.page.locator('.ant-picker')).toBeVisible();

    // El boton guardar debe estar deshabilitado si no hay aula seleccionada
    await attendancePage.expectSaveButtonDisabled();

    // La tabla debe mostrar el texto de guia (locale.emptyText del componente)
    await attendancePage.expectEmptyTableMessage();
  });

  test('TC-ATT-02: seleccionar aula carga los alumnos activos en la tabla', async ({
    attendancePage,
    apiHelper,
  }) => {
    // Obtener lista de aulas activas via API para saber cual seleccionar
    const token = await apiHelper.getAuthToken();
    const classrooms = await apiHelper.getClassrooms(token);

    if (classrooms.length === 0) {
      test.skip(true, 'No hay aulas activas disponibles para este test');
      return;
    }

    const firstClassroom = classrooms[0];
    const displayText = `${firstClassroom.nombre} (${firstClassroom.nivel})`;

    await attendancePage.goto();

    // Seleccionar el aula
    await attendancePage.selectAula(displayText);

    // La tabla debe mostrar alumnos (columnas: #, DNI, Alumno, Estado)
    const headers = attendancePage.page.locator('.ant-table-thead th');
    await expect(headers.getByText('DNI')).toBeVisible();
    await expect(headers.getByText('Alumno')).toBeVisible();
    await expect(headers.getByText('Estado')).toBeVisible();

    // El boton guardar debe habilitarse si hay alumnos
    const studentCount = await attendancePage.getStudentCount();
    if (studentCount > 0) {
      await expect(attendancePage.saveButton).toBeEnabled();
    }

    // Cada fila debe tener un Select con estado (por defecto PRESENTE)
    if (studentCount > 0) {
      const firstRowEstado = await attendancePage.getEstadoInRow(0);
      expect(firstRowEstado).toBeTruthy();
    }
  });

  test('TC-ATT-03: guardar asistencia con estados mixtos registra correctamente', async ({
    attendancePage,
    apiHelper,
  }) => {
    const token = await apiHelper.getAuthToken();
    const classrooms = await apiHelper.getClassrooms(token);

    if (classrooms.length === 0) {
      test.skip(true, 'No hay aulas activas disponibles para este test');
      return;
    }

    const firstClassroom = classrooms[0];
    const displayText = `${firstClassroom.nombre} (${firstClassroom.nivel})`;

    await attendancePage.goto();

    // Seleccionar aula
    await attendancePage.selectAula(displayText);

    const studentCount = await attendancePage.getStudentCount();
    if (studentCount === 0) {
      test.skip(true, 'El aula seleccionada no tiene alumnos activos');
      return;
    }

    // Marcar el primer alumno como PRESENTE (es el default, pero lo confirmamos)
    await attendancePage.setEstadoAlumno(0, 'PRESENTE');

    // Si hay mas alumnos, marcar el segundo como AUSENTE para tener datos mixtos
    if (studentCount >= 2) {
      await attendancePage.setEstadoAlumno(1, 'AUSENTE');
    }

    // Si hay un tercero, marcarlo como TARDANZA
    if (studentCount >= 3) {
      await attendancePage.setEstadoAlumno(2, 'TARDANZA');
    }

    // Guardar asistencia
    await attendancePage.saveAttendance();

    // El mensaje de exito confirma que el endpoint /attendance/registro-masivo/ respondio OK
    // El boton debe volver a estar enabled (no loading)
    await expect(attendancePage.saveButton).toBeEnabled({ timeout: 5000 });
  });
});
