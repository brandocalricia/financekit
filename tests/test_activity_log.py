"""Tests for activity logging utility."""
import os
import json
import shutil
import pytest
from unittest.mock import patch

TEST_DIR = os.path.join(os.path.dirname(__file__), "_test_data_activity")


@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def test_log_activity():
    from utils.activity_log import log_activity, get_recent
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        log_activity("added", "budget_tracker", "Added $500 to Housing budget")
        recent = get_recent(limit=5)
        assert len(recent) == 1
        assert recent[0]["action"] == "added"
        assert recent[0]["module"] == "budget_tracker"


def test_get_recent_empty():
    from utils.activity_log import get_recent
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        recent = get_recent()
        assert recent == []


def test_get_recent_limit():
    from utils.activity_log import log_activity, get_recent
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        for i in range(15):
            log_activity("action", "test", f"Entry {i}")
        recent = get_recent(limit=5)
        assert len(recent) == 5


def test_format_activity():
    from utils.activity_log import format_activity
    entry = {
        "action": "added",
        "module": "budget_tracker",
        "description": "Added receipt",
        "timestamp": "2024-01-01T12:00:00",
    }
    result = format_activity(entry)
    assert "Added receipt" in result
    assert "Added receipt" in result  # icon removed per no-emoji rule


def test_format_activity_unknown_module():
    from utils.activity_log import format_activity
    entry = {
        "action": "test",
        "module": "unknown_module",
        "description": "Test action",
        "timestamp": "2024-01-01T12:00:00",
    }
    result = format_activity(entry)
    assert "Test action" in result  # icon removed per no-emoji rule
