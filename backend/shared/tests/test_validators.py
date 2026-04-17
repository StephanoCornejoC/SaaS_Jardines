"""Unit tests for shared.validators -- no DB required."""

import pytest
from datetime import date

from rest_framework.exceptions import ValidationError

from shared.validators import validate_date_param, validate_month_param, validate_year_param


class TestValidateDateParam:
    def test_valid_date(self):
        result = validate_date_param("2026-04-15")
        assert result == date(2026, 4, 15)

    def test_none_returns_none(self):
        assert validate_date_param(None) is None

    def test_empty_string_returns_none(self):
        assert validate_date_param("") is None

    def test_invalid_format(self):
        with pytest.raises(ValidationError) as exc:
            validate_date_param("15/04/2026")
        assert "fecha" in str(exc.value.detail)

    def test_invalid_date_value(self):
        with pytest.raises(ValidationError):
            validate_date_param("2026-13-45")

    def test_garbage_string(self):
        with pytest.raises(ValidationError):
            validate_date_param("not-a-date")

    def test_custom_param_name(self):
        with pytest.raises(ValidationError) as exc:
            validate_date_param("invalid", "fecha_desde")
        assert "fecha_desde" in str(exc.value.detail)


class TestValidateMonthParam:
    def test_valid_months(self):
        assert validate_month_param("1") == 1
        assert validate_month_param("6") == 6
        assert validate_month_param("12") == 12

    def test_none_returns_none(self):
        assert validate_month_param(None) is None

    def test_empty_string_returns_none(self):
        assert validate_month_param("") is None

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_month_param("0")

    def test_thirteen(self):
        with pytest.raises(ValidationError):
            validate_month_param("13")

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_month_param("-1")

    def test_non_numeric(self):
        with pytest.raises(ValidationError):
            validate_month_param("abc")


class TestValidateYearParam:
    def test_valid_year(self):
        assert validate_year_param("2026") == 2026

    def test_none_returns_none(self):
        assert validate_year_param(None) is None

    def test_empty_string_returns_none(self):
        assert validate_year_param("") is None

    def test_too_low(self):
        with pytest.raises(ValidationError):
            validate_year_param("1999")

    def test_too_high(self):
        with pytest.raises(ValidationError):
            validate_year_param("2101")

    def test_non_numeric(self):
        with pytest.raises(ValidationError):
            validate_year_param("abcd")
