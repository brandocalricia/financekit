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
