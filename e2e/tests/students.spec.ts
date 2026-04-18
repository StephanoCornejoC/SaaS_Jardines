/**
 * TESTS: Alumnos (CRUD completo)
 *
 * Prerequisito: sesion activa con rol ADMIN_JARDIN o DIRECTOR.
 * Setup de datos via API para independencia entre tests.
 *
 * Cubre:
 * - TC-STU-01: Lista de alumnos carga y muestra tabla con datos
 * - TC-STU-02: Crear nuevo alumno con formulario valido
 * - TC-STU-03: Validacion de formulario - campos requeridos
 * - TC-STU-04: Editar alumno existente
 * - TC-STU-05: Buscar alumno por nombre muestra resultados filtrados
 * - TC-STU-06: Ver detalle de alumno navega a /alumnos/:id
 */
import { test, expect } from '../fixtures/auth';

// DNI unico por ejecucion para evitar colisiones en la base de datos
const uniqueDni = () => `9${Date.now().toString().slice(-7)}`;

test.describe('Alumnos - Lista y CRUD', () => {
  test('TC-STU-01: lista de alumnos carga la tabla con columnas correctas', async ({
    studentsPage,
  }) => {
    await studentsPage.goto();

    // El heading debe ser visible
    await expect(studentsPage.heading).toBeVisible();

    // La tabla debe estar presente
    await expect(studentsPage.studentsTable).toBeVisible();

    // Las columnas esperadas deben estar en los headers de la tabla
    const headers = studentsPage.page.locator('.ant-table-thead th');
    await expect(headers.getByText('DNI')).toBeVisible();
    await expect(headers.getByText('Nombres')).toBeVisible();
    await expect(headers.getByText('Apellidos')).toBeVisible();
    await expect(headers.getByText('Estado')).toBeVisible();
    await expect(headers.getByText('Acciones')).toBeVisible();

    // El boton "Nuevo Alumno" debe estar disponible
    await expect(studentsPage.newStudentButton).toBeVisible();
  });

  test('TC-STU-02: crear nuevo alumno con datos validos registra el alumno exitosamente', async ({
    studentsPage,
    apiHelper,
  }) => {
    await studentsPage.goto();

    const dni = uniqueDni();
    const nombres = 'Juan Carlos';
    const apellidos = 'Quispe Mamani';

    // Abrir modal de creacion
    await studentsPage.openCreateModal();

    // Llenar el formulario
    await studentsPage.fillStudentForm({
      dni,
      nombres,
      apellidos,
      fechaNacimiento: '15/01/2020',
      genero: 'Masculino',
    });

    // Guardar
    await studentsPage.submitModal();

    // Verificar mensaje de exito de Ant Design
    await studentsPage.expectSuccessMessage('Alumno creado');

    // El alumno debe aparecer en la tabla (buscar por DNI para certeza)
    await studentsPage.searchStudent(dni);
    await expect(studentsPage.tableRows.first()).toBeVisible();
    const dniEnTabla = await studentsPage.getColumnValueInRow(0, 0);
    expect(dniEnTabla).toBe(dni);

    // Cleanup: eliminar el alumno creado via la tabla
    // (En un entorno real se haria via API en afterAll)
    await studentsPage.deleteStudent(0);
    await studentsPage.expectSuccessMessage('Alumno eliminado');
  });

  test('TC-STU-03: formulario con campos vacios muestra errores de validacion inline', async ({
    studentsPage,
  }) => {
    await studentsPage.goto();
    await studentsPage.openCreateModal();

    // Intentar guardar sin llenar ningun campo
    await studentsPage.modalOkButton.click();

    // Ant Design Form valida y muestra errores bajo cada campo requerido
    await studentsPage.expectModalValidationError('DNI', 'Ingrese el DNI');
    await studentsPage.expectModalValidationError('Nombres', 'Ingrese los nombres');
    await studentsPage.expectModalValidationError('Apellidos', 'Ingrese los apellidos');
    await studentsPage.expectModalValidationError('Fecha de Nacimiento', 'Seleccione la fecha');
    await studentsPage.expectModalValidationError('Genero', 'Seleccione genero');

    // El modal debe seguir abierto
    await expect(studentsPage.modal).toBeVisible();

    // Cancelar para limpiar estado
    await studentsPage.cancelModal();
  });

  test('TC-STU-04: editar alumno existente actualiza los datos correctamente', async ({
    studentsPage,
    apiHelper,
  }) => {
    // Setup: crear alumno via API para tener datos predecibles
    const token = await apiHelper.getAuthToken();
    const student = await apiHelper.createStudent(token, {
      dni: uniqueDni(),
      nombres: 'Maria',
      apellidos: 'Lopez',
      fecha_nacimiento: '2019-06-20',
      genero: 'F',
    });

    await studentsPage.goto();

    // Buscar el alumno creado
    await studentsPage.searchStudent(student.dni!);

    // Abrir modal de edicion para la primera fila
    await studentsPage.openEditModal(0);

    // Verificar que el modal muestra los datos del alumno (modo edicion)
    await expect(studentsPage.modalTitle).toHaveText('Editar Alumno');

    // Modificar el nombre (los demas campos estan pre-llenados correctamente)
    await studentsPage.nombresInput.clear();
    await studentsPage.nombresInput.fill('Maria Elena');

    await studentsPage.submitModal();

    // Verificar mensaje de exito
    await studentsPage.expectSuccessMessage('Alumno actualizado');

    // Verificar que el cambio se refleja en la tabla
    await studentsPage.searchStudent(student.dni!);
    const nombresEnTabla = await studentsPage.getColumnValueInRow(0, 1);
    expect(nombresEnTabla).toContain('Maria Elena');

    // Cleanup
    await apiHelper.deleteStudent(token, student.id!);
  });

  test('TC-STU-05: buscar por nombre filtra la tabla con resultados relevantes', async ({
    studentsPage,
    apiHelper,
  }) => {
    // Setup: crear alumno con nombre unico para que la busqueda sea determinista
    const token = await apiHelper.getAuthToken();
    const uniqueName = `ZZTestBusqueda${Date.now()}`;
    const student = await apiHelper.createStudent(token, {
      dni: uniqueDni(),
      nombres: uniqueName,
      apellidos: 'Prueba',
      fecha_nacimiento: '2021-03-10',
      genero: 'M',
    });

    await studentsPage.goto();

    // Buscar por el nombre unico
    await studentsPage.searchStudent(uniqueName);

    // Solo debe aparecer el alumno que coincide
    const count = await studentsPage.getRowCount();
    expect(count).toBe(1);

    // El nombre en la tabla debe contener el termino buscado
    const nombresEnTabla = await studentsPage.getColumnValueInRow(0, 1);
    expect(nombresEnTabla).toContain(uniqueName);

    // Cleanup
    await apiHelper.deleteStudent(token, student.id!);
  });

  test('TC-STU-06: boton ver alumno navega a la pagina de detalle /alumnos/:id', async ({
    studentsPage,
    apiHelper,
  }) => {
    // Setup: asegurar que hay al menos un alumno
    const token = await apiHelper.getAuthToken();
    const student = await apiHelper.createStudent(token, {
      dni: uniqueDni(),
      nombres: 'Pedro',
      apellidos: 'Castro',
      fecha_nacimiento: '2020-09-05',
      genero: 'M',
    });

    await studentsPage.goto();
    await studentsPage.searchStudent(student.dni!);

    // Hacer click en el icono de ver (EyeOutlined)
    await studentsPage.clickViewStudent(0);

    // La URL debe cambiar a /alumnos/:id
    await expect(studentsPage.page).toHaveURL(
      new RegExp(`/alumnos/${student.id!}`)
    );

    // La pagina de detalle debe mostrar el nombre del alumno
    const heading = studentsPage.page.getByRole('heading', { level: 4 });
    await expect(heading).toContainText('Pedro Castro');

    // Cleanup
    await apiHelper.deleteStudent(token, student.id!);
  });
});
