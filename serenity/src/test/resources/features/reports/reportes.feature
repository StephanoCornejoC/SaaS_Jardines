# language: es
@reportes
Característica: Descarga de Reportes Excel
  Como administrador del jardin
  Quiero descargar reportes en formato Excel
  Para analizar la informacion del jardin fuera del sistema

  @lista-reportes @tc-rep-01
  Escenario: TC-REP-01 Pagina de reportes muestra las 4 tarjetas de descarga
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Reportes
    Entonces el encabezado "Reportes" es visible
    Y la tarjeta "Reporte de Morosidad" es visible
    Y la tarjeta "Lista de Alumnos" es visible
    Y la tarjeta "Reporte de Asistencia" es visible
    Y la tarjeta "Reporte de Caja" es visible
    Y hay exactamente 4 botones "Descargar Excel"

  @descargar-excel @tc-rep-02
  Escenario: TC-REP-02 Descargar Lista de Alumnos inicia descarga del archivo xlsx
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Reportes
    Cuando hago clic en "Descargar Excel" de la tarjeta "Lista de Alumnos"
    Entonces se inicia la descarga del archivo "lista_alumnos.xlsx"
    Y aparece el mensaje de exito "Lista de Alumnos descargado"

  @estado-loading @tc-rep-03
  Escenario: TC-REP-03 Boton de descarga muestra estado loading durante la peticion
    Dado que tengo una sesion activa como administrador
    Y navego al modulo de Reportes
    Cuando hago clic en "Descargar Excel" de la tarjeta "Reporte de Morosidad"
    Entonces el boton muestra el estado de carga con la clase ant-btn-loading
    Y cuando la descarga completa el boton vuelve al estado normal
