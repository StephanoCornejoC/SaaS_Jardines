package com.corem.saas.tasks;

import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.targets.Target;
import net.serenitybdd.annotations.Step;

/**
 * Task: Marcar el estado de asistencia de un alumno en la tabla de asistencia.
 *
 * El estado se selecciona via un Select de Ant Design dentro de la fila de la tabla.
 * Estados validos: PRESENTE, AUSENTE, TARDANZA
 */
public class MarkAttendance implements Task {

    private final int rowIndex;
    private final String estado;

    private MarkAttendance(int rowIndex, String estado) {
        this.rowIndex = rowIndex;
        this.estado = estado;
    }

    public static MarkAttendance forStudent(int rowIndex) {
        return new MarkAttendance(rowIndex, "PRESENTE");
    }

    public MarkAttendance as(String estado) {
        return new MarkAttendance(rowIndex, estado);
    }

    public static MarkAttendance forStudentAtRow(int rowIndex, String estado) {
        return new MarkAttendance(rowIndex, estado);
    }

    @Override
    @Step("{0} marca el alumno en la fila #rowIndex como '#estado'")
    public <T extends Actor> void performAs(T actor) {
        // Localizar el Select de estado en la fila especifica
        Target rowSelect = Target.the("selector de estado en fila " + rowIndex)
            .locatedBy(".ant-table-tbody tr.ant-table-row:nth-of-type(" + (rowIndex + 1) + ") .ant-select");

        actor.attemptsTo(
            Click.on(rowSelect),
            SelectFromAntdDropdown.withOption(estado).from(rowSelect)
        );
    }
}
