# language: es
@navegacion
Característica: Navegacion y Control de Acceso
  Como usuario del sistema
  Quiero que la navegacion sea coherente y las rutas esten protegidas
  Para garantizar la seguridad y usabilidad del sistema

  @menu-lateral @tc-nav-01
  Escenario: TC-NAV-01 El sidebar navega correctamente a cada modulo principal
    Dado que tengo una sesion activa como administrador
    Y navego al dashboard
    Y espero que el dashboard cargue completamente
    Cuando navego a cada modulo desde el menu lateral:
      | etiqueta          | url_esperada     |
      | Alumnos           | /alumnos         |
      | Profesores        | /profesores      |
      | Aulas             | /aulas           |
      | Matriculas        | /matriculas      |
      | Pensiones         | /pensiones       |
      | Flujo de Caja     | /caja            |
      | Asistencia        | /asistencia      |
      | Comunicaciones    | /comunicaciones  |
      | Reportes          | /reportes        |
    Entonces cada modulo carga sin errores de spinner

  @menu-activo @tc-nav-02
  Escenario: TC-NAV-02 El item del menu activo tiene la clase selected de Ant Design
    Dado que tengo una sesion activa como administrador
    Y navego a "/alumnos"
    Entonces el encabezado "Alumnos" es visible
    Y el item "Alumnos" del menu lateral tiene la clase "ant-menu-item-selected"

  @colapsar-sidebar @tc-nav-03
  Escenario: TC-NAV-03 El boton de colapsar sidebar reduce el ancho del menu
    Dado que tengo una sesion activa como administrador
    Y navego al dashboard
    Cuando hago clic en el boton de colapsar el sidebar
    Entonces el sidebar tiene la clase "ant-layout-sider-collapsed"
    Cuando hago clic de nuevo en el boton de colapsar
    Entonces el sidebar no tiene la clase "ant-layout-sider-collapsed"

  @ruta-privada-sin-sesion @tc-nav-04
  Escenario: TC-NAV-04 Acceder a ruta privada sin sesion redirige a login
    Dado que soy un usuario sin sesion activa
    Cuando navego directamente a "/dashboard"
    Entonces soy redirigido a la pagina de login

  @alumno-sin-sesion @tc-nav-05
  Escenario: TC-NAV-05 Acceder a modulo alumnos sin sesion redirige a login
    Dado que soy un usuario sin sesion activa
    Cuando navego directamente a "/alumnos"
    Entonces soy redirigido a la pagina de login

  @ruta-desconocida-sin-sesion @tc-nav-06
  Escenario: TC-NAV-06 Ruta desconocida sin sesion redirige a login
    Dado que soy un usuario sin sesion activa
    Cuando navego directamente a "/ruta-inexistente"
    Entonces soy redirigido a la pagina de login

  @ruta-desconocida-con-sesion @tc-nav-07
  Escenario: TC-NAV-07 Ruta desconocida con sesion activa redirige al dashboard
    Dado que tengo una sesion activa como administrador
    Cuando navego directamente a "/modulo-que-no-existe"
    Entonces soy redirigido al dashboard
    Y el encabezado "Dashboard" es visible
