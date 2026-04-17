# language: es
@alumnos
Característica: Gestion de Alumnos (CRUD completo)
  Como administrador del jardin
  Quiero gestionar el registro de alumnos
  Para mantener actualizada la informacion de los estudiantes

  @lista-alumnos @tc-stu-01
  Escenario: TC-STU-01 Lista de alumnos carga la tabla con columnas correctas
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Alumnos
    Entonces el encabezado "Alumnos" es visible
    Y la tabla de alumnos esta presente
    Y la tabla contiene las columnas "DNI", "Nombres", "Apellidos", "Estado", "Acciones"
    Y el boton "Nuevo Alumno" esta disponible

  @crear-alumno @tc-stu-02
  Escenario: TC-STU-02 Crear nuevo alumno con datos validos lo registra exitosamente
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Alumnos
    Cuando abro el modal de creacion de alumno
    Y lleno el formulario con los datos del alumno:
      | campo             | valor       |
      | DNI               | 99887766    |
      | Nombres           | Juan Carlos |
      | Apellidos         | Quispe Test |
      | Fecha Nacimiento  | 15/01/2020  |
      | Genero            | Masculino   |
    Y guardo el formulario
    Entonces aparece el mensaje de exito "Alumno creado"
    Y el alumno con DNI "99887766" aparece en la tabla

  @validacion-alumno @tc-stu-03
  Escenario: TC-STU-03 Formulario con campos vacios muestra errores de validacion
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Alumnos
    Cuando abro el modal de creacion de alumno
    Y intento guardar el formulario sin llenar ningun campo
    Entonces el modal muestra el error "Ingrese el DNI" en el campo "DNI"
    Y el modal muestra el error "Ingrese los nombres" en el campo "Nombres"
    Y el modal muestra el error "Ingrese los apellidos" en el campo "Apellidos"
    Y el modal muestra el error "Seleccione la fecha" en el campo "Fecha de Nacimiento"
    Y el modal muestra el error "Seleccione genero" en el campo "Genero"
    Y el modal de alumno permanece abierto

  @editar-alumno @tc-stu-04
  Escenario: TC-STU-04 Editar alumno existente actualiza los datos correctamente
    Dado que tengo una sesion activa como administrador
    Y existe un alumno con DNI "98765432" y nombre "Maria Lopez" creado via API
    Y navego al modulo de Alumnos
    Cuando busco el alumno por DNI "98765432"
    Y abro el modal de edicion del primer resultado
    Entonces el titulo del modal es "Editar Alumno"
    Cuando modifico el nombre a "Maria Elena"
    Y guardo el formulario
    Entonces aparece el mensaje de exito "Alumno actualizado"
    Y el nombre "Maria Elena" aparece en la tabla para el DNI "98765432"

  @buscar-alumno @tc-stu-05
  Escenario: TC-STU-05 Buscar por nombre filtra la tabla con resultados relevantes
    Dado que tengo una sesion activa como administrador
    Y existe un alumno con nombre unico "ZZTestBusquedaUnique" creado via API
    Y navego al modulo de Alumnos
    Cuando busco el alumno por nombre "ZZTestBusquedaUnique"
    Entonces la tabla muestra exactamente 1 resultado
    Y el nombre "ZZTestBusquedaUnique" aparece en la primera fila de la tabla

  @detalle-alumno @tc-stu-06
  Escenario: TC-STU-06 Ver detalle de alumno navega a la pagina de detalle
    Dado que tengo una sesion activa como administrador
    Y existe un alumno con DNI "97654321" y nombre "Pedro Castro" creado via API
    Y navego al modulo de Alumnos
    Cuando busco el alumno por DNI "97654321"
    Y hago clic en el icono de ver del primer resultado
    Entonces la URL contiene "/alumnos/"
    Y la pagina de detalle muestra el nombre "Pedro Castro"
