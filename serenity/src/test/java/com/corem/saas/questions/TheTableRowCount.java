package com.corem.saas.questions;

import com.corem.saas.ui.CoremTargets;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;
import net.serenitybdd.screenplay.annotations.Subject;
import net.serenitybdd.screenplay.targets.Target;

/**
 * Question: Cuenta las filas visibles en la tabla de Ant Design.
 *
 * Uso:
 *   int count = actor.asksFor(TheTableRowCount.inTheCurrentTable());
 *   actor.should(seeThat(TheTableRowCount.inTheCurrentTable(), equalTo(1)));
 */
@Subject("el numero de filas en la tabla")
public class TheTableRowCount implements Question<Integer> {

    private final Target tableTarget;

    private TheTableRowCount(Target tableTarget) {
        this.tableTarget = tableTarget;
    }

    public static TheTableRowCount inTheCurrentTable() {
        return new TheTableRowCount(CoremTargets.ANT_TABLE_ROWS);
    }

    public static TheTableRowCount in(Target tableTarget) {
        return new TheTableRowCount(tableTarget);
    }

    @Override
    public Integer answeredBy(Actor actor) {
        try {
            return tableTarget.resolveAllFor(actor).size();
        } catch (Exception e) {
            return 0;
        }
    }
}
