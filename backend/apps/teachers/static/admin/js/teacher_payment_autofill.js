/* Pre-llenado automático del monto en el admin de TeacherPayment (Sueldos).
 *
 * Cuando Stephano elige un contrato en el FK `contract`, el campo `monto`
 * se pre-llena con el sueldo del contrato seleccionado. Si el monto ya
 * tenía un valor, NO lo sobrescribe (respetamos lo que el usuario tipeó
 * — puede ser un bono o ajuste).
 *
 * Cada option de #id_contract tiene un atributo data-sueldo inyectado
 * desde el server (ver formfield_for_foreignkey en TeacherPaymentAdmin).
 */
(function () {
  function setup() {
    var $ = window.django && window.django.jQuery;
    if (!$) { return setTimeout(setup, 100); }

    var $contract = $('#id_contract');
    var $monto = $('#id_monto');
    if (!$contract.length || !$monto.length) return;

    $contract.on('change', function () {
      var $selected = $contract.find('option:selected');
      var sueldo = $selected.attr('data-sueldo');
      var current = $monto.val();
      if (sueldo && (!current || parseFloat(current) === 0)) {
        $monto.val(sueldo);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
