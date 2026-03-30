"""Tests for spending insights engine."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_no_data_no_crash(temp_data_dir):
    """Empty data should produce no insights, not crash."""
    from utils.insights import generate_insights
    result = generate_insights()
    assert isinstance(result, list)


def test_get_top_insight_no_data(temp_data_dir):
    from utils.insights import get_top_insight
    result = get_top_insight()
    assert result is None or isinstance(result, dict)


def _write_transactions(data_dir, transactions):
    """Helper to write budget_transactions.json into temp data dir."""
    import json
    fp = os.path.join(data_dir, "budget_transactions.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(transactions, f)


def test_anomaly_detection_normal(temp_data_dir):
    """No anomalies when spending is consistent across months."""
    from utils.insights import detect_anomalies

    txns = []
    # 4 months of consistent $100/month in Groceries
    for month in range(1, 5):
        for day in (5, 15, 25):
            txns.append({
                "date": f"2026-{month:02d}-{day:02d}",
                "description": "Grocery Store",
                "amount": 33.33,
                "category": "Groceries",
                "month": f"2026-{month:02d}",
            })

    _write_transactions(temp_data_dir, txns)

    anomalies = detect_anomalies()
    # All months ~$100 each, no category should spike >50%
    cat_anomalies = [a for a in anomalies if a.get("category") == "Groceries"
                     and "above" in a.get("description", "")]
    assert len(cat_anomalies) == 0


def test_anomaly_detection_spike(temp_data_dir):
    """Spending spike should trigger an anomaly."""
    from utils.insights import detect_anomalies

    txns = []
    # 3 prior months: ~$100/month in Dining
    for month in range(1, 4):
        txns.append({
            "date": f"2026-{month:02d}-10",
            "description": "Restaurant",
            "amount": 100.0,
            "category": "Dining",
            "month": f"2026-{month:02d}",
        })

    # Current month (month 4): $600 — a 6x spike (500% above avg)
    txns.append({
        "date": "2026-04-10",
        "description": "Fancy Restaurant",
        "amount": 600.0,
        "category": "Dining",
        "month": "2026-04",
    })

    _write_transactions(temp_data_dir, txns)

    anomalies = detect_anomalies()
    dining_anomalies = [a for a in anomalies if a.get("category") == "Dining"]
    assert len(dining_anomalies) > 0
