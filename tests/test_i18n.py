"""Tests for the i18n translation module."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(autouse=True)
def mock_session_state(monkeypatch):
    """Patch streamlit.session_state so i18n.t() works without Streamlit."""
    import streamlit
    monkeypatch.setattr(streamlit, "session_state", {"language": "en"})


def _set_language(monkeypatch, lang: str):
    import streamlit
    monkeypatch.setattr(streamlit, "session_state", {"language": lang})


def test_t_returns_english_default():
    from utils.i18n import t
    assert t("dashboard") == "Dashboard"


def test_t_returns_spanish(monkeypatch):
    _set_language(monkeypatch, "es")
    from utils.i18n import t
    assert t("dashboard") == "Panel"


def test_t_missing_key_fallback(monkeypatch):
    """A key that exists in English but is missing in Spanish falls back to English."""
    _set_language(monkeypatch, "es")
    from utils.i18n import t, _STRINGS

    # Find a key that exists in en but not in es (or test a synthetic one)
    # Use a known-good English key — if es has it, the fallback logic still works
    # We'll verify the fallback mechanism by temporarily removing a key
    en_keys = set(_STRINGS["en"].keys())
    es_keys = set(_STRINGS["es"].keys())
    missing_in_es = en_keys - es_keys

    if missing_in_es:
        key = next(iter(missing_in_es))
        result = t(key)
        assert result == _STRINGS["en"][key]
    else:
        # All keys present — inject a test key into English only
        _STRINGS["en"]["_test_fallback_xyz"] = "Fallback Value"
        try:
            result = t("_test_fallback_xyz")
            assert result == "Fallback Value"
        finally:
            del _STRINGS["en"]["_test_fallback_xyz"]


def test_t_unknown_key_returns_key():
    from utils.i18n import t
    assert t("completely_unknown_xyz") == "completely_unknown_xyz"


def test_t_parameterized():
    from utils.i18n import t
    assert t("days_ago", n=5) == "5 days ago"


def test_all_keys_complete():
    from utils.i18n import _STRINGS
    en_keys = set(_STRINGS["en"].keys())
    for lang in ("es", "fr", "de"):
        lang_keys = set(_STRINGS[lang].keys())
        missing = en_keys - lang_keys
        assert not missing, f"Language '{lang}' is missing keys: {missing}"


def test_available_languages():
    from utils.i18n import AVAILABLE_LANGUAGES
    assert len(AVAILABLE_LANGUAGES) == 4
