"""Tests for the category learning system."""
import json
import os
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


def test_learn_and_retrieve():
    """Learned corrections should be retrievable."""
    from utils.category_learner import learn_from_correction, get_learned_category

    learn_from_correction("STARBUCKS #12345", "Other", "Dining Out")
    assert get_learned_category("STARBUCKS #12345") == "Dining Out"


def test_fuzzy_match_variation():
    """Fuzzy matching should catch variations of the same merchant."""
    from utils.category_learner import learn_from_correction, get_learned_category

    learn_from_correction("STARBUCKS COFFEE #12345 NYC", "Other", "Dining Out")
    # Different store number should still match
    result = get_learned_category("STARBUCKS COFFEE #67890 NYC")
    assert result == "Dining Out"


def test_no_match_returns_none():
    """Unrelated descriptions should not match."""
    from utils.category_learner import learn_from_correction, get_learned_category

    learn_from_correction("NETFLIX SUBSCRIPTION", "Other", "Entertainment")
    result = get_learned_category("WALMART GROCERY")
    assert result is None


def test_same_category_no_op():
    """Learning with same old/new category should be a no-op."""
    from utils.category_learner import learn_from_correction, get_all_rules

    learn_from_correction("SOME STORE", "Shopping", "Shopping")
    assert len(get_all_rules()) == 0


def test_repeated_correction_increments_count():
    """Multiple corrections for the same pattern should increase times_used."""
    from utils.category_learner import learn_from_correction, get_all_rules

    learn_from_correction("TARGET #1234", "Other", "Shopping")
    learn_from_correction("TARGET #5678", "Other", "Shopping")

    rules = get_all_rules()
    assert len(rules) == 1
    assert rules[0]["times_used"] == 2
    assert rules[0]["confidence"] > 0.6


def test_override_with_different_category():
    """A new correction for the same pattern with a different category should update."""
    from utils.category_learner import learn_from_correction, get_learned_category

    learn_from_correction("CVS PHARMACY", "Other", "Health")
    learn_from_correction("CVS PHARMACY", "Health", "Shopping")
    assert get_learned_category("CVS PHARMACY") == "Shopping"


def test_rules_by_category():
    """get_rules_by_category should return correct counts."""
    from utils.category_learner import learn_from_correction, get_rules_by_category

    learn_from_correction("WALMART SUPERCENTER", "Other", "Shopping")
    learn_from_correction("TARGET CORPORATION", "Other", "Shopping")
    learn_from_correction("OLIVE GARDEN ITALIAN", "Other", "Dining Out")

    counts = get_rules_by_category()
    assert counts.get("Shopping", 0) == 2
    assert counts.get("Dining Out", 0) == 1


def test_delete_rule():
    """delete_rule should remove a learned rule."""
    from utils.category_learner import learn_from_correction, delete_rule, get_all_rules, _normalize

    learn_from_correction("MY STORE XYZ", "Other", "Shopping")
    assert len(get_all_rules()) == 1

    pattern = _normalize("MY STORE XYZ")
    delete_rule(pattern)
    assert len(get_all_rules()) == 0


def test_is_learned():
    """is_learned should return True for learned patterns."""
    from utils.category_learner import learn_from_correction, is_learned

    learn_from_correction("WHOLE FOODS MKT", "Other", "Food & Groceries")
    assert is_learned("WHOLE FOODS MKT") is True
    assert is_learned("RANDOM UNKNOWN STORE") is False


def test_empty_description():
    """Empty description should be handled gracefully."""
    from utils.category_learner import learn_from_correction, get_learned_category

    learn_from_correction("", "Other", "Shopping")
    assert get_learned_category("") is None
