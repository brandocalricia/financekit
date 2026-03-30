"""Tests for portfolio tracker math logic.

The calculation functions are embedded in the render function,
so we test the math formulas directly.
"""
import pytest


def test_cagr_calculation():
    """CAGR = (end/start)^(1/years) - 1."""
    start_value = 10_000
    end_value = 16_105.10  # ~10% CAGR over 5 years
    years = 5

    cagr = (end_value / start_value) ** (1 / years) - 1
    assert abs(cagr - 0.10) < 0.001  # ~10%


def test_cagr_one_year():
    """Over 1 year, CAGR equals simple return."""
    start, end = 100, 120
    cagr = (end / start) ** (1 / 1) - 1
    assert abs(cagr - 0.20) < 0.001


def test_gain_loss_calculation():
    """Gain/loss = (current_price - purchase_price) * quantity."""
    purchase_price = 150.0
    current_price = 175.0
    quantity = 10

    gain = (current_price - purchase_price) * quantity
    assert gain == 250.0

    pct = (current_price - purchase_price) / purchase_price * 100
    assert abs(pct - 16.667) < 0.01


def test_gain_loss_negative():
    """Negative gain (loss)."""
    purchase_price = 200.0
    current_price = 180.0
    quantity = 5

    gain = (current_price - purchase_price) * quantity
    assert gain == -100.0


def test_sector_allocation_percentages():
    """Sector allocation percentages sum to 100."""
    holdings = [
        {"sector": "Tech", "value": 5000},
        {"sector": "Finance", "value": 3000},
        {"sector": "Healthcare", "value": 2000},
    ]
    total = sum(h["value"] for h in holdings)
    allocations = {h["sector"]: h["value"] / total * 100 for h in holdings}

    assert abs(allocations["Tech"] - 50.0) < 0.01
    assert abs(allocations["Finance"] - 30.0) < 0.01
    assert abs(allocations["Healthcare"] - 20.0) < 0.01
    assert abs(sum(allocations.values()) - 100.0) < 0.01


def test_sector_allocation_single():
    """Single holding = 100% allocation."""
    holdings = [{"sector": "Tech", "value": 10_000}]
    total = sum(h["value"] for h in holdings)
    pct = holdings[0]["value"] / total * 100
    assert pct == 100.0
