"""Tests for formatting utilities."""
import pytest
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.formatting import format_currency, format_currency_int, format_date, parse_date


def test_format_currency_usd():
    result = format_currency(1234.56)
    assert "1,234.56" in result


def test_format_currency_zero():
    result = format_currency(0)
    assert "0.00" in result


def test_format_currency_none():
    result = format_currency(None)
    assert "0.00" in result


def test_format_currency_negative():
    result = format_currency(-500.50)
    assert "500.50" in result


def test_format_currency_int():
    result = format_currency_int(1234.56)
    assert "1,235" in result


def test_format_currency_int_none():
    result = format_currency_int(None)
    assert "0" in result


def test_format_date_datetime():
    dt = datetime(2026, 3, 29)
    result = format_date(dt)
    # Default is MM/DD/YYYY
    assert "2026" in result or "03" in result


def test_format_date_string():
    result = format_date("2026-03-29")
    assert result  # Should produce non-empty string


def test_format_date_empty():
    result = format_date("")
    assert result == ""


def test_parse_date_iso():
    result = parse_date("2026-03-29")
    assert result is not None
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 29


def test_parse_date_us():
    result = parse_date("03/29/2026")
    assert result is not None
    assert result.year == 2026


def test_parse_date_invalid():
    result = parse_date("not a date")
    assert result is None


def test_parse_date_none():
    result = parse_date(None)
    assert result is None
