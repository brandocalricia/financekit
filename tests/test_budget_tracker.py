"""Tests for budget tracker utilities."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.budget_tracker import _categorize, DEFAULT_CATEGORIES, CATEGORY_MAP


def test_category_mapping_known():
    """Known vendors should map to correct categories."""
    assert _categorize("WALMART SUPERCENTER #1234") == "Food & Groceries"
    assert _categorize("SHELL GAS STATION") == "Transportation"
    assert _categorize("NETFLIX.COM") == "Entertainment"


def test_category_mapping_unknown():
    """Unknown vendors should fall back to 'Other'."""
    result = _categorize("RANDOM_VENDOR_XYZ_12345")
    assert result == "Other"


def test_default_categories_exist():
    """Default categories list should have entries."""
    assert len(DEFAULT_CATEGORIES) > 0
    assert "Food & Groceries" in DEFAULT_CATEGORIES
    assert "Entertainment" in DEFAULT_CATEGORIES


def test_category_map_not_empty():
    """Category mapping should have entries."""
    assert len(CATEGORY_MAP) > 0
