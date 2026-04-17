# language: es
@flujo-de-caja
Característica: Flujo de Caja
  Como administrador del jardin
  Quiero gestionar las transacciones de ingresos y egresos
  Para mantener un control financiero preciso del jardin

  @estadisticas-caja @tc-cash-01
  Escenario: TC-CASH-01 Cards de resumen muestran ingresos, egresos y balance del mes
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Caja
    Entonces la card de "Ingresos" del mes es visible
    Y la card de "Egresos" del mes es visible
    Y la card de "Balance" del mes es visible
    Y los valores de las cards son numericos
    Y el tab "Transacciones" esta activo por defecto

  @nueva-transaccion @tc-cash-02
  Escenario: TC-CASH-02 Crear nueva transaccion INGRESO la agrega a la tabla
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Caja
    Cuando cuento las transacciones actuales en la tabla
    Y abro el modal de nueva transaccion
    Y lleno el formulario de transaccion:
      | campo       | valor             |
      | Tipo        | Ingreso           |
      | Categoria   | Otros             |
      | Descripcion | Test E2E Ingreso  |
      | Monto       | 150.50            |
      | Fecha       | 08/04/2026        |
    Y guardo la transaccion
    Entonces aparece el mensaje de exito "Transaccion registrada"
    Y la tabla tiene una transaccion mas que antes
    Y la descripcion "Test E2E Ingreso" aparece en la tabla

  @validacion-transaccion @tc-cash-03
  Escenario: TC-CASH-03 Formulario de transaccion valida campos requeridos
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Caja
    Cuando abro el modal de nueva transaccion
    Y intento guardar la transaccion sin llenar ningun campo
    Entonces el modal muestra errores de validacion en los campos requeridos:
      | campo       |
      | Tipo        |
      | Categoria   |
      | Descripcion |
      | Monto       |
      | Fecha       |
    Y el modal de transaccion permanece abierto
    Cuando cancelo el modal de transaccion
    Entonces el modal de transaccion esta oculto

  @cierres-mensuales @tc-cash-04
  Escenario: TC-CASH-04 Tab de Cierres Mensuales muestra la tabla de cierres historicos
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Caja
    Cuando hago clic en el tab "Cierres Mensuales"
    Entonces el tab "Cierres Mensuales" esta activo
    Y la tabla de cierres es visible
    Y la tabla de cierres contiene las columnas "Mes", "Ano", "Total Ingresos", "Total Egresos", "Balance", "Estado"
