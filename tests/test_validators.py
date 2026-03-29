"""Tests for JSON data schema validation and repair."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.validators import validate_and_repair


def test_valid_data_passes():
    data = {
        "_schema_version": 1,
        "holdings": [{"ticker": "AAPL"}],
        "alerts": [],
        "watchlist": [],
        "trade_history": [],
    }
    result = validate_and_repair("portfolio.json", data)
    assert result["holdings"] == [{"ticker": "AAPL"}]
    assert result["_schema_version"] == 1


def test_missing_keys_repaired():
    data = {"holdings": []}
    result = validate_and_repair("portfolio.json", data)
    assert "alerts" in result
    assert "watchlist" in result
    assert "trade_history" in result
    assert isinstance(result["alerts"], list)


def test_type_mismatch_repaired():
    data = {
        "_schema_version": "1",  # string instead of int
        "user_name": 123,  # int instead of str
        "user_email": "",
        "currency": {"code": "USD", "symbol": "$"},
        "date_format": "MM/DD/YYYY",
        "theme": "dark",
    }
    result = validate_and_repair("settings.json", data)
    assert isinstance(result["user_name"], str)


def test_unknown_keys_preserved():
    data = {
        "_schema_version": 1,
        "holdings": [],
        "alerts": [],
        "watchlist": [],
        "trade_history": [],
        "custom_field": "should_stay",
    }
    result = validate_and_repair("portfolio.json", data)
    assert result["custom_field"] == "should_stay"


def test_list_type_validation():
    # Pass a dict where list is expected
    data = {"wrong": "type"}
    result = validate_and_repair("receipts.json", data)
    assert isinstance(result, list)


def test_no_schema_passes_through():
    data = {"anything": "goes"}
    result = validate_and_repair("unknown_file.json", data)
    assert result == data


def test_freelance_repair():
    data = {"clients": []}
    result = validate_and_repair("freelance_data.json", data)
    assert "invoices" in result
    assert "time_entries" in result
    assert "recurring_invoices" in result
    assert "expenses" in result


def test_list_item_repair():
    data = [
        {"id": "abc", "vendor": "Store"},  # missing other fields
    ]
    result = validate_and_repair("receipts.json", data)
    assert result[0]["category"] == "Other"
    assert result[0]["total"] == 0.0
