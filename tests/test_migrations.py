"""Tests for data migration framework."""
import os
import json
import shutil
import pytest
from unittest.mock import patch

TEST_DIR = os.path.join(os.path.dirname(__file__), "_test_data_migrations")


@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def _write_json(filename, data):
    with open(os.path.join(TEST_DIR, filename), "w") as f:
        json.dump(data, f)


def test_freelance_migration():
    from utils.migrations import _freelance_v0_to_v1
    data = {}
    result = _freelance_v0_to_v1(data)
    assert "clients" in result
    assert "invoices" in result
    assert "time_entries" in result
    assert "expenses" in result
    assert result["_schema_version"] == 1


def test_portfolio_migration():
    from utils.migrations import _portfolio_v0_to_v1
    data = {"holdings": [{"ticker": "AAPL", "quantity": 10, "purchase_price": 150}]}
    result = _portfolio_v0_to_v1(data)
    assert "watchlist" in result
    assert "trade_history" in result
    assert result["holdings"][0]["dividend_yield"] == 0
    assert result["_schema_version"] == 1


def test_settings_migration_v0_v1():
    from utils.migrations import _settings_v0_to_v1
    data = {"user_name": "Test"}
    result = _settings_v0_to_v1(data)
    assert "notifications" in result
    assert "invoice" in result
    assert result["_schema_version"] == 1


def test_settings_migration_v1_v2():
    from utils.migrations import _settings_v1_to_v2
    data = {"_schema_version": 1}
    result = _settings_v1_to_v2(data)
    assert "enabled_modules" in result
    assert "onboarding_complete" in result
    assert result["_schema_version"] == 2


def test_budgets_migration():
    from utils.migrations import _budgets_v0_to_v1
    data = {}
    result = _budgets_v0_to_v1(data)
    assert "categories" in result
    assert result["_schema_version"] == 1


def test_get_schema_version():
    from utils.migrations import get_schema_version
    assert get_schema_version({"_schema_version": 3}) == 3
    assert get_schema_version({}) == 0
    assert get_schema_version([]) == 0


def test_run_migrations():
    from utils.migrations import run_migrations
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        _write_json("freelance_data.json", {})
        applied = run_migrations()
        assert len(applied) >= 1


def test_check_pending():
    from utils.migrations import check_pending
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        _write_json("settings.json", {})
        pending = check_pending()
        assert len(pending) >= 1
