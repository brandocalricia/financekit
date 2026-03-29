"""Shared test fixtures for FinanceKit test suite."""
import json
import os
import sys
import tempfile
import shutil
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Create a temporary data directory and redirect data_persistence to it."""
    import utils.data_persistence as dp
    data_dir = str(tmp_path / "data")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "backups"), exist_ok=True)

    monkeypatch.setattr(dp, "DATA_DIR", data_dir)
    monkeypatch.setattr(dp, "BACKUP_DIR", os.path.join(data_dir, "backups"))
    monkeypatch.setattr(dp, "_user_data_dir", None)
    return data_dir


@pytest.fixture
def sample_settings():
    return {
        "user_name": "Test User",
        "user_email": "test@example.com",
        "currency": {"code": "USD", "symbol": "$"},
        "date_format": "MM/DD/YYYY",
        "theme": "dark",
        "_schema_version": 1,
    }


@pytest.fixture
def sample_goals():
    return [
        {
            "id": "abc123",
            "name": "Emergency Fund",
            "target": 10000.0,
            "current": 5000.0,
            "deadline": "2026-12-31",
            "monthly": 500.0,
            "history": [],
        }
    ]


@pytest.fixture
def sample_portfolio():
    return {
        "holdings": [
            {
                "ticker": "AAPL",
                "type": "Stock",
                "purchase_price": 150.0,
                "quantity": 10,
                "added": "2025-01-01",
                "dividend_yield": 0.5,
                "sector": "Technology",
            }
        ],
        "alerts": [],
        "watchlist": [],
        "trade_history": [],
        "_schema_version": 1,
    }


@pytest.fixture
def sample_freelance():
    return {
        "clients": [
            {
                "id": "cl01",
                "client": "Acme Corp",
                "project": "Website Redesign",
                "date_started": "2026-01-15",
                "status": "In Progress",
                "client_status": "Active",
                "rate_type": "Hourly",
                "rate": 75.0,
                "email": "acme@example.com",
                "notes": "",
            }
        ],
        "invoices": [
            {
                "id": "inv01",
                "number": "INV-2026-0001",
                "client": "Acme Corp",
                "date": "2026-02-01",
                "due_date": "2026-03-03",
                "amount": 2250.0,
                "line_items": [{"description": "Dev work", "quantity": 30, "rate": 75}],
                "paid": True,
                "paid_date": "2026-02-28",
                "payment_terms": "Net 30",
            }
        ],
        "time_entries": [],
        "recurring_invoices": [],
        "expenses": [],
        "_schema_version": 1,
    }
