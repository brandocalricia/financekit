"""Tests for household management utilities."""
import os
import json
import pytest
from unittest.mock import patch

# Patch DATA_DIR before importing
TEST_DIR = os.path.join(os.path.dirname(__file__), "_test_data_household")


@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        yield
    # Cleanup
    import shutil
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def _write(filename, data):
    path = os.path.join(TEST_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f)


def _read(filename):
    path = os.path.join(TEST_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def test_enable_household():
    from utils.household import enable_household, get_household
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        hh = enable_household("The Smiths", "Alice")
        assert hh["enabled"] is True
        assert hh["name"] == "The Smiths"
        assert len(hh["members"]) == 1
        assert hh["members"][0]["name"] == "Alice"
        assert hh["members"][0]["role"] == "owner"
        assert len(hh["invite_code"]) == 6


def test_disable_household():
    from utils.household import enable_household, disable_household, get_household
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        enable_household("Test", "Owner")
        disable_household()
        hh = get_household()
        assert hh["enabled"] is False


def test_add_remove_member():
    from utils.household import enable_household, add_member, remove_member, get_members
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        enable_household("Family", "Parent")
        member = add_member("Child")
        members = get_members()
        assert len(members) == 2
        assert members[1]["name"] == "Child"

        remove_member(member["id"])
        members = get_members()
        assert len(members) == 1


def test_join_household():
    from utils.household import enable_household, join_household, get_household
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        hh = enable_household("Home", "Alice")
        code = hh["invite_code"]

        member, msg = join_household(code, "Bob")
        assert member is not None
        assert member["name"] == "Bob"

        # Invalid code
        member2, msg2 = join_household("WRONG1", "Eve")
        assert member2 is None
        assert "Invalid" in msg2

        # Duplicate name
        member3, msg3 = join_household(code, "Bob")
        assert member3 is None


def test_create_split_even():
    from utils.household import create_split, get_balances
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        split = create_split("Dinner", 100.0, "Alice", ["Bob"], method="even")
        assert split["total"] == 100.0
        assert split["shares"]["Alice"] == 50.0
        assert split["shares"]["Bob"] == 50.0

        balances = get_balances()
        assert ("Bob", "Alice") in balances
        assert balances[("Bob", "Alice")] == 50.0


def test_settle_split():
    from utils.household import create_split, settle_split, get_unsettled_splits, get_balances
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        split = create_split("Groceries", 80.0, "Alice", ["Bob"], method="even")
        assert len(get_unsettled_splits()) == 1

        settle_split(split["id"])
        assert len(get_unsettled_splits()) == 0
        assert len(get_balances()) == 0


def test_one_paid_split():
    from utils.household import create_split, get_balances
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        split = create_split("Rent", 1200.0, "Alice", ["Bob", "Charlie"], method="one_paid")
        balances = get_balances()
        assert ("Bob", "Alice") in balances
        assert ("Charlie", "Alice") in balances
        assert balances[("Bob", "Alice")] == 600.0


def test_member_names():
    from utils.household import enable_household, add_member, get_member_names
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        enable_household("Home", "Alice")
        add_member("Bob")
        names = get_member_names()
        assert "Alice" in names
        assert "Bob" in names


def test_is_household_enabled():
    from utils.household import is_household_enabled, enable_household
    with patch("utils.data_persistence.DATA_DIR", TEST_DIR):
        assert is_household_enabled() is False
        enable_household("Test", "Owner")
        assert is_household_enabled() is True
