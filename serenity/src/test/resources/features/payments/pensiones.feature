# language: es
@pensiones
Característica: Gestion de Pensiones y Pagos
  Como administrador del jardin
  Quiero gestionar los pagos de pensiones
  Para mantener el control financiero de los alumnos

  @lista-pensiones @tc-pay-01
  Escenario: TC-PAY-01 Lista de pensiones carga tabla con columnas y filtros
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Pensiones
    Entonces el encabezado "Pensiones" es visible
    Y la tabla de pensiones esta presente
    Y la tabla contiene las columnas "Alumno", "Mes", "Estado", "Acciones"
    Y los filtros de mes, anio y estado estan disponibles

  @filtrar-pensiones @tc-pay-02
  Escenario: TC-PAY-02 Filtrar por estado PAGADO muestra solo pagos pagados
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Pensiones
    Cuando filtro las pensiones por estado "Pagado"
    Entonces todos los registros visibles tienen el estado "PAGADO"

  @registrar-pago @tc-pay-03
  Escenario: TC-PAY-03 Registrar pago cambia el estado del registro a PAGADO
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Pensiones
    Y filtro las pensiones por estado "Pendiente"
    Dado que existen pensiones pendientes en la tabla
    Cuando abro el modal de pago del primer registro pendiente
    Entonces el modal "Registrar Pago" esta visible
    Y el campo monto tiene un valor pre-rellenado
    Cuando selecciono el metodo de pago "Efectivo"
    Y agrego las observaciones "Pago test automatizado"
    Y confirmo el pago
    Entonces aparece el mensaje de exito "Pago registrado"
    Y el registro ya no aparece como pendiente

  @generar-qr @tc-pay-04
  Escenario: TC-PAY-04 Boton QR abre modal con imagen de codigo QR
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Pensiones
    Dado que existen pensiones en la tabla
    Cuando hago clic en el boton de QR del primer registro
    Entonces el modal de QR esta visible
    Y la imagen del codigo QR tiene dimensiones mayores a cero
    Cuando cierro el modal de QR
    Entonces el modal de QR esta oculto
