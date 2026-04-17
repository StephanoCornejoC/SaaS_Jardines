from datetime import datetime

from rest_framework.exceptions import ValidationError


def validate_date_param(value, param_name="fecha"):
    """Valida y parsea un parametro de fecha (YYYY-MM-DD). Retorna date o None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValidationError(
            {param_name: f"Formato de fecha invalido: '{value}'. Use YYYY-MM-DD."}
        )


def validate_month_param(value, param_name="mes"):
    """Valida un parametro de mes (1-12). Retorna int o None."""
    if not value:
        return None
    try:
        month = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            {param_name: f"Mes invalido: '{value}'. Debe ser un numero entre 1 y 12."}
        )
    if month < 1 or month > 12:
        raise ValidationError(
            {param_name: f"Mes fuera de rango: {month}. Debe ser entre 1 y 12."}
        )
    return month


def validate_year_param(value, param_name="anio"):
    """Valida un parametro de anio (2000-2100). Retorna int o None."""
    if not value:
        return None
    try:
        year = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            {param_name: f"Anio invalido: '{value}'. Debe ser un numero."}
        )
    if year < 2000 or year > 2100:
        raise ValidationError(
            {param_name: f"Anio fuera de rango: {year}. Debe ser entre 2000 y 2100."}
        )
    return year
