"""Tests for fuzzy transaction matching."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.fuzzy_matcher import normalize_description, group_similar_transactions


def test_normalize_removes_dates():
    result = normalize_description("NETFLIX 03/15/2026 Payment")
    assert "03/15/2026" not in result
    assert "netflix" in result


def test_normalize_removes_refs():
    result = normalize_description("Payment ref: ABC123 to Spotify")
    assert "abc123" not in result.lower()
    assert "spotify" in result


def test_normalize_strips_whitespace():
    result = normalize_description("  NETFLIX   INC   ")
    assert result == "netflix inc"


def test_group_similar():
    descs = [
        "NETFLIX INC 03/15",
        "Netflix Inc 04/15",
        "NETFLIX INC",
        "SPOTIFY USA",
        "Spotify",
        "RANDOM PURCHASE",
    ]
    groups = group_similar_transactions(descs, threshold=70)
    # Netflix entries should be grouped
    netflix_found = False
    for key, indices in groups.items():
        if "netflix" in key.lower() or "NETFLIX" in key:
            netflix_found = True
            assert len(indices) >= 2
    assert netflix_found


def test_threshold_sensitivity():
    descs = ["NETFLIX INC", "Netflix", "NET FLIX", "NETFLOX"]
    # Low threshold = more aggressive grouping
    groups_low = group_similar_transactions(descs, threshold=50)
    groups_high = group_similar_transactions(descs, threshold=95)
    # Low threshold should produce fewer groups (more merged)
    assert len(groups_low) <= len(groups_high)


def test_empty_input():
    groups = group_similar_transactions([])
    assert groups == {}


def test_single_input():
    groups = group_similar_transactions(["NETFLIX"])
    assert len(groups) == 1
