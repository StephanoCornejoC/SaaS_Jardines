/* Filtro dinámico de categorías en el admin de CashTransaction.
 *
 * Espejo de la lógica del frontend de Caja: cuando el SuperAdmin elige
 * "INGRESO" en el select de tipo, las opciones del select de categoría
 * se filtran para mostrar solo las categorías de tipo INGRESO. Idem
 * EGRESO. Esto evita el bug de mezclar tipo y categoría (ej. INGRESO +
 * "Sueldos" que es EGRESO), que rompía el cierre de caja.
 *
 * Cada option de #id_categoria tiene un atributo data-tipo inyectado
 * desde el server (ver formfield_for_foreignkey en CashTransactionAdmin).
 */
(function () {
  function setup() {
    var $ = window.django && window.django.jQuery;
    if (!$) { return setTimeout(setup, 100); }

    var $tipo = $('#id_tipo');
    var $categoria = $('#id_categoria');
    if (!$tipo.length || !$categoria.length) return;

    var originalOptions = $categoria.find('option').clone(true);

    function applyFilter() {
      var tipo = $tipo.val();
      var current = $categoria.val();
      $categoria.empty();
      originalOptions.each(function () {
        var $opt = $(this);
        var optTipo = $opt.attr('data-tipo');
        if (!tipo || !optTipo || optTipo === tipo || $opt.val() === '') {
          $categoria.append($opt.clone(true));
        }
      });
      // Restaurar selección si aún es válida tras el filtro
      if (current && $categoria.find('option[value="' + current + '"]').length) {
        $categoria.val(current);
      } else {
        $categoria.val('');
      }
    }

    $tipo.on('change', applyFilter);
    applyFilter();  // aplicar al cargar (caso edición)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
