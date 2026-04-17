from datetime import date
from decimal import Decimal


def get_current_school_year():
    """
    Retorna el año escolar actual.
    En Perú el año escolar coincide con el año calendario (marzo - diciembre).
    Si estamos en enero o febrero, se considera el año anterior.
    """
    today = date.today()
    if today.month <= 2:
        return today.year - 1
    return today.year


def format_currency(amount):
    """
    Formatea un monto numérico como moneda peruana.
    Ejemplo: 1234.56 -> "S/ 1,234.56"
    """
    if amount is None:
        return "S/ 0.00"

    amount = Decimal(str(amount))
    sign = "-" if amount < 0 else ""
    amount = abs(amount)

    integer_part = int(amount)
    decimal_part = amount - integer_part

    # Formatear con separador de miles
    formatted_int = f"{integer_part:,}"
    formatted_decimal = f"{decimal_part:.2f}"[1:]  # ".56"

    return f"{sign}S/ {formatted_int}{formatted_decimal}"
