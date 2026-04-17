package com.corem.saas.tasks;

import com.corem.saas.interactions.SelectFromAntdDropdown;
import com.corem.saas.interactions.TypeInAntdPicker;
import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Clear;
import net.serenitybdd.screenplay.actions.Click;
import net.serenitybdd.screenplay.actions.Enter;
import net.serenitybdd.annotations.Step;

/**
 * Task: Crear un nuevo alumno a traves del formulario modal.
 *
 * Requiere estar en la pagina /alumnos con el modal de creacion ya abierto,
 * o usa OpenNewStudentModal como prerequisito.
 *
 * Uso:
 *   actor.attemptsTo(
 *     OpenNewStudentModal.fromTheStudentList(),
 *     CreateStudent.withData("99887766", "Juan", "Quispe", "15/01/2020", "Masculino")
 *   );
 */
public class CreateStudent implements Task {

    private final String dni;
    private final String nombres;
    private final String apellidos;
    private final String fechaNacimiento;
    private final String genero;

    private CreateStudent(String dni, String nombres, String apellidos,
                          String fechaNacimiento, String genero) {
        this.dni = dni;
        this.nombres = nombres;
        this.apellidos = apellidos;
        this.fechaNacimiento = fechaNacimiento;
        this.genero = genero;
    }

    public static CreateStudent withData(String dni, String nombres, String apellidos,
                                         String fechaNacimiento, String genero) {
        return new CreateStudent(dni, nombres, apellidos, fechaNacimiento, genero);
    }

    @Override
    @Step("{0} llena el formulario de alumno con DNI '#dni'")
    public <T extends Actor> void performAs(T actor) {
        // Llenar DNI
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNO_FORM_DNI),
            Enter.theValue(dni).into(CoremTargets.ALUMNO_FORM_DNI)
        );

        // Llenar Nombres
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNO_FORM_NOMBRES),
            Enter.theValue(nombres).into(CoremTargets.ALUMNO_FORM_NOMBRES)
        );

        // Llenar Apellidos
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNO_FORM_APELLIDOS),
            Enter.theValue(apellidos).into(CoremTargets.ALUMNO_FORM_APELLIDOS)
        );

        // Fecha de nacimiento (DatePicker de Ant Design)
        actor.attemptsTo(
            TypeInAntdPicker.withValue(fechaNacimiento)
                .in(CoremTargets.ALUMNO_FORM_FECHA_NACIMIENTO)
        );

        // Genero (Select de Ant Design)
        actor.attemptsTo(
            Click.on(CoremTargets.ALUMNO_FORM_GENERO),
            SelectFromAntdDropdown.withOption(genero).from(CoremTargets.ALUMNO_FORM_GENERO)
        );
    }
}
