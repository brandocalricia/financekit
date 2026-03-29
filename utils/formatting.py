"""Centralized currency and date formatting utilities.

Reads user preferences from data/settings.json and provides consistent
formatting across all modules.
"""
import os
import json
from datetime import datetime, date

_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "settings.json"
)

_DEFAULT_SETTINGS = {
    "currency": {"code": "USD", "symbol": "$"},
    "date_format": "MM/DD/YYYY",
}

_DATE_FORMAT_MAP = {
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
}


def _get_settings():
    """Load settings from disk. Returns defaults if file missing."""
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return _DEFAULT_SETTINGS


def get_currency_symbol():
    """Return the user's configured currency symbol (e.g. '$', '\u20ac')."""
    settings = _get_settings()
    return settings.get("currency", {}).get("symbol", "$")


def format_currency(amount, show_sign=False):
    """Format a number as currency using the user's preferred symbol.

    Args:
        amount: The numeric amount to format.
        show_sign: If True, prefix with +/- for positive/negative values.

    Returns:
        Formatted string like "$1,234.56" or "\u20ac1.234,56".
    """
    symbol = get_currency_symbol()
    if amount is None:
        return f"{symbol}0.00"
    amount = float(amount)
    if show_sign:
        return f"{symbol}{amount:+,.2f}"
    return f"{symbol}{amount:,.2f}"


def format_currency_int(amount):
    """Format a number as currency with no decimals.

    Returns:
        Formatted string like "$1,235" or "\u20ac1.235".
    """
    symbol = get_currency_symbol()
    if amount is None:
        return f"{symbol}0"
    return f"{symbol}{float(amount):,.0f}"


def format_date(date_input):
    """Format a date according to the user's preferred format.

    Args:
        date_input: A datetime, date object, or date string (ISO format).

    Returns:
        Formatted date string, or the original string if parsing fails.
    """
    settings = _get_settings()
    fmt_key = settings.get("date_format", "MM/DD/YYYY")
    fmt = _DATE_FORMAT_MAP.get(fmt_key, "%m/%d/%Y")

    if isinstance(date_input, datetime):
        return date_input.strftime(fmt)
    if isinstance(date_input, date):
        return date_input.strftime(fmt)
    if isinstance(date_input, str) and date_input.strip():
        for parse_fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
            try:
                dt = datetime.strptime(date_input.strip(), parse_fmt)
                return dt.strftime(fmt)
            except ValueError:
                continue
    return str(date_input) if date_input else ""


def parse_date(date_str):
    """Parse a date string in various formats into a datetime object.

    Args:
        date_str: A date string in any common format.

    Returns:
        A datetime object, or None if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S",
                "%b %d, %Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None
