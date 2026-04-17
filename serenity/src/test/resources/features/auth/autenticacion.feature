# language: es
@autenticacion
Característica: Autenticacion de usuarios
  Como administrador del jardin
  Quiero poder iniciar y cerrar sesion de forma segura
  Para proteger la informacion del sistema

  Antecedentes:
    Dado que el sistema COREM esta disponible en http://localhost:3000

  @login @tc-auth-01
  Escenario: TC-AUTH-01 Login exitoso redirige al dashboard
    Dado que soy un usuario sin sesion activa
    Y navego a la pagina de login
    Entonces veo los campos de email, contrasena y el boton de ingresar
    Cuando ingreso las credenciales validas "admin@test.com" y "TestPass1234"
    Y hago clic en el boton Ingresar
    Entonces soy redirigido al dashboard
    Y el encabezado "Dashboard" es visible
    Y mi email aparece en el encabezado de la aplicacion

  @login-fallido @tc-auth-02
  Escenario: TC-AUTH-02 Credenciales invalidas muestra mensaje de error
    Dado que soy un usuario sin sesion activa
    Y navego a la pagina de login
    Cuando ingreso las credenciales invalidas "usuario@invalido.com" y "contrasenaMala123"
    Y hago clic en el boton Ingresar
    Entonces aparece el mensaje de error de Ant Design "Credenciales incorrectas"
    Y permanezco en la pagina de login
    Y el formulario de login sigue visible

  @validacion @tc-auth-03
  Escenario: TC-AUTH-03 Validacion de campos vacios muestra errores inline
    Dado que soy un usuario sin sesion activa
    Y navego a la pagina de login
    Cuando hago clic en el boton Ingresar sin llenar ningun campo
    Entonces el campo "Correo electronico" muestra el error "Ingrese su correo"
    Y el campo "Contrasena" muestra el error "Ingrese su contrasena"
    Y permanezco en la pagina de login

  @logout @tc-auth-04
  Escenario: TC-AUTH-04 Logout limpia la sesion y redirige a login
    Dado que tengo una sesion activa como administrador
    Y navego al dashboard
    Cuando hago clic en el boton Salir del encabezado
    Entonces soy redirigido a la pagina de login
    Y al intentar navegar a "/dashboard" soy redirigido a login
    Y el token de acceso no existe en el almacenamiento local
