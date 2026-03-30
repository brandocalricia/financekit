"""Tests for bill tracking functionality."""
import json
import os
from datetime import date, datetime
import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    """Redirect data storage to a temp directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    def mock_path(filename):
        return str(data_dir / filename)

    monkeypatch.setattr("utils.data_persistence._path", mock_path)
    return data_dir


def _make_bill(name="Netflix", amount=15.99, due_day=15, frequency="monthly",
               auto_pay=False, last_paid="", active=True):
    return {
        "id": name.lower()[:8],
        "name": name,
        "amount": amount,
        "due_day": due_day,
        "frequency": frequency,
        "category": "Subscriptions",
        "auto_pay": auto_pay,
        "last_paid": last_paid,
        "notes": "",
        "active": active,
    }


def test_save_and_load_bills():
    """Bills should round-trip through save/load."""
    from modules.budget_tracker import _save_bills, _load_bills
    bills = [_make_bill("Netflix"), _make_bill("Spotify", amount=9.99, due_day=1)]
    _save_bills(bills)
    loaded = _load_bills()
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Netflix"
    assert loaded[1]["amount"] == 9.99


def test_overdue_detection():
    """A bill past its due day without payment this month should be overdue."""
    from modules.budget_tracker import _is_overdue
    today = date.today()
    # Bill due on day 1 — if today is past day 1, it's overdue
    if today.day > 1:
        bill = _make_bill(due_day=1)
        assert _is_overdue(bill) is True


def test_not_overdue_when_paid():
    """A bill marked paid this month should not be overdue."""
    from modules.budget_tracker import _is_overdue
    today = date.today()
    if today.day > 1:
        bill = _make_bill(due_day=1, last_paid=today.isoformat())
        assert _is_overdue(bill) is False


def test_next_due_date_this_month():
    """If due day hasn't passed, next due is this month."""
    from modules.budget_tracker import _next_due_date
    today = date.today()
    # Due on day 28 — if today is before 28, should be this month
    if today.day < 28:
        bill = _make_bill(due_day=28)
        result = _next_due_date(bill)
        assert result.month == today.month
        assert result.day == 28


def test_next_due_date_next_month():
    """If due day has passed, next due is next month."""
    from modules.budget_tracker import _next_due_date
    today = date.today()
    if today.day > 1:
        bill = _make_bill(due_day=1)
        result = _next_due_date(bill)
        # Should be next month (or later)
        assert result >= today


def test_get_upcoming_bills():
    """get_upcoming_bills returns active bills due within N days."""
    from modules.budget_tracker import _save_bills, get_upcoming_bills
    today = date.today()
    # Create bill due on same day of month
    bills = [
        _make_bill("Test Bill", due_day=today.day),
        _make_bill("Inactive", due_day=today.day, active=False),
    ]
    _save_bills(bills)
    upcoming = get_upcoming_bills(30)
    names = [u["name"] for u in upcoming]
    assert "Test Bill" in names
    assert "Inactive" not in names


def test_detect_bills_from_transactions():
    """detect_bills_from_transactions should find recurring charges."""
    from utils.insights import detect_bills_from_transactions

    # Create 3 months of "Netflix" charges on day 15
    txns = []
    for month in [1, 2, 3]:
        txns.append({
            "date": f"2025-{month:02d}-15",
            "description": "NETFLIX SUBSCRIPTION",
            "amount": 15.99,
            "category": "Entertainment",
        })

    suggestions = detect_bills_from_transactions(txns)
    assert len(suggestions) >= 1
    assert any("NETFLIX" in s["name"].upper() for s in suggestions)


def test_empty_bills_list():
    """Empty bills list should be handled gracefully."""
    from modules.budget_tracker import _save_bills, _load_bills, get_upcoming_bills, get_overdue_bills
    _save_bills([])
    assert _load_bills() == []
    assert get_upcoming_bills() == []
    assert get_overdue_bills() == []
