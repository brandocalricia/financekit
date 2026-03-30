"""Tests for utils/formatting.py — currency, date, and number formatting."""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_settings():
    """Default to USD settings."""
    with patch("utils.formatting._get_settings", return_value={
        "currency": {"code": "USD", "symbol": "$"},
        "date_format": "MM/DD/YYYY",
    }):
        yield


def test_get_currency_symbol_usd():
    from utils.formatting import get_currency_symbol
    assert get_currency_symbol() == "$"


def test_get_currency_symbol_eur():
    with patch("utils.formatting._get_settings", return_value={
        "currency": {"code": "EUR", "symbol": "\u20ac"},
    }):
        from utils.formatting import get_currency_symbol
        assert get_currency_symbol() == "\u20ac"


def test_get_currency_symbol_gbp():
    with patch("utils.formatting._get_settings", return_value={
        "currency": {"code": "GBP", "symbol": "\u00a3"},
    }):
        from utils.formatting import get_currency_symbol
        assert get_currency_symbol() == "\u00a3"


def test_get_currency_symbol_jpy():
    with patch("utils.formatting._get_settings", return_value={
        "currency": {"code": "JPY", "symbol": "\u00a5"},
    }):
        from utils.formatting import get_currency_symbol
        assert get_currency_symbol() == "\u00a5"


def test_format_currency_basic():
    from utils.formatting import format_currency
    result = format_currency(1234.56)
    assert result == "$1,234.56"


def test_format_currency_none():
    from utils.formatting import format_currency
    assert format_currency(None) == "$0.00"


def test_format_currency_negative():
    from utils.formatting import format_currency
    result = format_currency(-500.25)
    assert "-500.25" in result


def test_format_currency_with_sign():
    from utils.formatting import format_currency
    result = format_currency(100, show_sign=True)
    assert "+" in result


def test_format_currency_large_number():
    from utils.formatting import format_currency
    result = format_currency(1_500_000)
    assert "1,500,000" in result


def test_format_currency_int():
    from utils.formatting import format_currency_int
    result = format_currency_int(1234.56)
    assert result == "$1,235"


def test_format_date_iso_string():
    from utils.formatting import format_date
    result = format_date("2024-03-15")
    assert result == "03/15/2024"


def test_format_date_datetime():
    from utils.formatting import format_date
    from datetime import datetime
    result = format_date(datetime(2024, 3, 15))
    assert result == "03/15/2024"


def test_format_date_invalid_returns_original():
    from utils.formatting import format_date
    result = format_date("not-a-date")
    assert result == "not-a-date"
