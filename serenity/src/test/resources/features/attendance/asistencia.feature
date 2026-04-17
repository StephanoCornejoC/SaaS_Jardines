# language: es
@asistencia
Característica: Registro de Asistencia
  Como docente o administrador del jardin
  Quiero registrar la asistencia diaria de los alumnos
  Para tener un control preciso de la presencia en el aula

  @sin-aula @tc-att-01
  Escenario: TC-ATT-01 Sin seleccion de aula la tabla muestra mensaje de guia
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Asistencia
    Entonces el encabezado de asistencia es visible
    Y el selector de aula esta disponible
    Y el selector de fecha esta disponible
    Y el boton guardar esta deshabilitado
    Y la tabla muestra el mensaje de guia para seleccionar un aula

  @seleccionar-aula @tc-att-02
  Escenario: TC-ATT-02 Seleccionar aula carga los alumnos activos en la tabla
    Dado que tengo una sesion activa como administrador
    Y existen aulas activas disponibles en el sistema via API
    Y navego al modulo de Asistencia
    Cuando selecciono la primera aula disponible
    Entonces la tabla de asistencia muestra las columnas "DNI", "Alumno", "Estado"
    Y el boton guardar esta habilitado si el aula tiene alumnos
    Y los alumnos del aula tienen el estado "PRESENTE" por defecto

  @guardar-asistencia @tc-att-03
  Escenario: TC-ATT-03 Guardar asistencia con estados mixtos registra correctamente
    Dado que tengo una sesion activa como administrador
    Y existen aulas activas con alumnos en el sistema via API
    Y navego al modulo de Asistencia
    Cuando selecciono la primera aula disponible con alumnos
    Y marco el primer alumno como "PRESENTE"
    Y marco el segundo alumno como "AUSENTE" si existe
    Y marco el tercer alumno como "TARDANZA" si existe
    Y guardo la asistencia
    Entonces el boton guardar vuelve al estado habilitado
