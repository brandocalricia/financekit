"""Tests for utils/search.py — global search across data files."""
import json
import os
import pytest

from utils.search import search_all


@pytest.fixture
def seed_transactions(temp_data_dir):
    """Write sample transactions.json into the temp data dir."""
    txns = [
        {"description": "Costco Wholesale", "category": "Groceries", "amount": -124.50},
        {"description": "Netflix Subscription", "category": "Entertainment", "amount": -15.99},
    ]
    with open(os.path.join(temp_data_dir, "transactions.json"), "w") as f:
        json.dump(txns, f)
    return txns


@pytest.fixture
def seed_goals(temp_data_dir):
    """Write sample goals.json into the temp data dir."""
    goals = [
        {"name": "Emergency Fund", "target": 10000, "current": 4500},
        {"name": "Vacation Savings", "target": 3000, "current": 800},
    ]
    with open(os.path.join(temp_data_dir, "goals.json"), "w") as f:
        json.dump(goals, f)
    return goals


def test_search_finds_transactions(seed_transactions):
    results = search_all("costco")
    assert len(results) == 1
    assert results[0]["module"] == "Report Generator"
    assert "Costco" in results[0]["title"]


def test_search_finds_goals(seed_goals):
    results = search_all("emergency")
    assert len(results) == 1
    assert results[0]["module"] == "Goal Tracker"
    assert results[0]["title"] == "Emergency Fund"
    assert "$4,500" in results[0]["detail"]


def test_search_empty_query(temp_data_dir):
    assert search_all("") == []
    assert search_all("   ") == []
    assert search_all("a") == []  # fewer than 2 chars after strip


def test_search_no_results(seed_transactions, seed_goals):
    results = search_all("zzzyyyxxx")
    assert results == []
