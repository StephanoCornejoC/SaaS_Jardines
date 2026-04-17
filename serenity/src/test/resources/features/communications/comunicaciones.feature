# language: es
@comunicaciones
Característica: Libro de Comunicaciones
  Como administrador del jardin
  Quiero gestionar las comunicaciones hacia padres y apoderados
  Para mantener una comunicacion efectiva con la comunidad educativa

  @lista-comunicaciones @tc-comm-01
  Escenario: TC-COMM-01 Lista de comunicaciones carga la tabla con columnas correctas
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Comunicaciones
    Entonces el encabezado "Comunicaciones" es visible
    Y el spinner de carga desaparece
    Y la tabla de comunicaciones esta visible
    Y la tabla contiene las columnas "Titulo", "Tipo", "Estado"
    Y el boton "Nueva Comunicacion" esta disponible

  @crear-comunicacion @tc-comm-02
  Escenario: TC-COMM-02 Crear comunicacion GENERAL la registra en la tabla
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Comunicaciones
    Cuando abro el modal de nueva comunicacion
    Y el modal "Nueva Comunicacion" es visible
    Y lleno el titulo con "Comunicado Test Automatizado E2E"
    Y lleno el contenido con "Contenido del comunicado generado por test E2E automatizado"
    Y el campo "Aula" no es visible porque el tipo es GENERAL
    Y guardo la comunicacion
    Entonces el modal se cierra
    Y aparece el mensaje de exito "Comunicacion creada"
    Y el comunicado "Comunicado Test Automatizado E2E" aparece en la tabla

  @tipo-condicional @tc-comm-03
  Escenario: TC-COMM-03 Selector de aula aparece solo cuando el tipo es POR_AULA
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Comunicaciones
    Cuando abro el modal de nueva comunicacion
    Entonces el campo "Aula" no es visible porque el tipo es GENERAL
    Cuando cambio el tipo de comunicacion a "Por Aula"
    Entonces el campo "Aula" es visible en el modal
    Cuando cancelo el modal de comunicacion
    Entonces el modal de comunicacion esta oculto

  @enviar-comunicacion @tc-comm-04
  Escenario: TC-COMM-04 Enviar comunicacion via Popconfirm cambia estado a ENVIADO
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Comunicaciones
    Y el spinner de carga desaparece
    Dado que existen comunicaciones en estado BORRADOR
    Cuando hago clic en el boton Enviar de la primera comunicacion en borrador
    Entonces el Popconfirm de confirmacion es visible con el texto "Enviar esta comunicacion?"
    Cuando confirmo el envio en el Popconfirm
    Entonces aparece el mensaje de exito "Comunicacion enviada"
