# language: es
@dashboard
Característica: Dashboard y KPIs
  Como administrador del jardin
  Quiero ver los indicadores clave del negocio en el dashboard
  Para tener una vision rapida del estado del jardin

  @kpis @tc-dash-01
  Escenario: TC-DASH-01 Los cuatro KPIs se muestran con titulos y valores numericos
    Dado que tengo una sesion activa como administrador
    Y navego al dashboard
    Y espero que el dashboard cargue completamente
    Entonces el KPI "Total Alumnos" es visible con un valor numerico valido
    Y el KPI "Total Profesores" es visible con un valor numerico valido
    Y el KPI "Ingresos del Mes" es visible con un valor numerico valido
    Y el KPI "Morosidad" es visible con un valor numerico valido
    Y el menu lateral es visible

  @grafico @tc-dash-02
  Escenario: TC-DASH-02 El grafico de ingresos mensuales se renderiza correctamente
    Dado que tengo una sesion activa como administrador
    Y navego al dashboard
    Y espero que el dashboard cargue completamente
    Entonces el grafico de ingresos mensuales esta renderizado con dimensiones validas
    Y el card contenedor del grafico es visible
