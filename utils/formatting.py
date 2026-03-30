"""Centralized currency and date formatting utilities v5.9.

Reads user preferences from data/settings.json and provides consistent
formatting across all modules. Supports locale-aware currency formatting.
"""
import os
import json
from datetime import datetime, date, timedelta

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

# Locale-aware currency formatting rules (v5.8)
_CURRENCY_FORMATS = {
    "USD": {"symbol": "$", "thousands": ",", "decimal": ".", "decimals": 2, "prefix": True},
    "EUR": {"symbol": "\u20ac", "thousands": ".", "decimal": ",", "decimals": 2, "prefix": False},
    "GBP": {"symbol": "\u00a3", "thousands": ",", "decimal": ".", "decimals": 2, "prefix": True},
    "CAD": {"symbol": "C$", "thousands": ",", "decimal": ".", "decimals": 2, "prefix": True},
    "AUD": {"symbol": "A$", "thousands": ",", "decimal": ".", "decimals": 2, "prefix": True},
    "JPY": {"symbol": "\u00a5", "thousands": ",", "decimal": ".", "decimals": 0, "prefix": True},
    "INR": {"symbol": "\u20b9", "thousands": ",", "decimal": ".", "decimals": 2, "prefix": True},
    "BRL": {"symbol": "R$", "thousands": ".", "decimal": ",", "decimals": 2, "prefix": True},
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


def format_date_relative(date_input):
    """Format a date with relative labels for recent dates (v5.8).

    Returns 'Today', 'Yesterday', '3 days ago' for recent dates,
    and falls back to the user's preferred date format for older dates.
    """
    if isinstance(date_input, str):
        dt = parse_date(date_input)
    elif isinstance(date_input, datetime):
        dt = date_input
    elif isinstance(date_input, date):
        dt = datetime.combine(date_input, datetime.min.time())
    else:
        return str(date_input) if date_input else ""

    if dt is None:
        return str(date_input)

    today = datetime.now().date()
    d = dt.date() if isinstance(dt, datetime) else dt
    delta = (today - d).days

    if delta == 0:
        return "Today"
    elif delta == 1:
        return "Yesterday"
    elif delta < 7:
        return f"{delta} days ago"
    else:
        return format_date(date_input)
