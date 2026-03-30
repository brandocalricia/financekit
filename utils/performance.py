"""Performance utilities for FinanceKit v5.9.

Provides caching helpers, pagination, startup optimization,
and a health-check endpoint.
"""
import os
import json
import time
import streamlit as st
from datetime import datetime


# ---------------------------------------------------------------------------
# Cached data loading
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@st.cache_data(ttl=300, show_spinner=False)
def cached_load_json(filepath: str, _mtime: float):
    """Load and cache a JSON file.  Cache is busted when mtime changes.

    Args:
        filepath: Absolute path to the JSON file.
        _mtime: File modification time (used as cache key).

    Returns:
        Parsed JSON data, or None if the file can't be read.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def smart_load_json(filename: str, default=None):
    """Load JSON with st.cache_data, auto-busting on file change."""
    fp = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(fp):
        return default
    try:
        mtime = os.path.getmtime(fp)
    except OSError:
        return default
    data = cached_load_json(fp, mtime)
    return data if data is not None else default


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------

def paginate(items: list, page_key: str = "page", page_size: int = 50):
    """Return a page-slice of *items* and render page controls.

    Args:
        items: Full list of items.
        page_key: Unique session-state key for tracking current page.
        page_size: Number of items per page.

    Returns:
        Slice of items for the current page.
    """
    if not items or len(items) <= page_size:
        return items

    total_pages = (len(items) + page_size - 1) // page_size
    current = st.session_state.get(page_key, 1)
    current = max(1, min(current, total_pages))

    start = (current - 1) * page_size
    end = start + page_size

    # Render pagination controls
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current > 1:
            if st.button("← Previous", key=f"{page_key}_prev"):
                st.session_state[page_key] = current - 1
                st.rerun()
    with col_info:
        st.caption(f"Page {current} of {total_pages}  ({len(items)} items)")
    with col_next:
        if current < total_pages:
            if st.button("Next →", key=f"{page_key}_next"):
                st.session_state[page_key] = current + 1
                st.rerun()

    return items[start:end]


# ---------------------------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------------------------

def health_check() -> dict:
    """Run a quick health check and return status dict.

    Checks:
        - data directory exists and is writable
        - settings.json is valid JSON
        - key data files are readable
        - disk usage of data directory
    """
    checks = {}

    # Data dir
    data_dir = _DATA_DIR
    checks["data_dir_exists"] = os.path.isdir(data_dir)
    checks["data_dir_writable"] = os.access(data_dir, os.W_OK) if checks["data_dir_exists"] else False

    # Settings
    settings_path = os.path.join(data_dir, "settings.json")
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                json.load(f)
            checks["settings_valid"] = True
        else:
            checks["settings_valid"] = None  # not yet created
    except Exception:
        checks["settings_valid"] = False

    # Key files
    key_files = [
        "budgets.json", "goals.json", "portfolio.json",
        "receipts.json", "budget_transactions.json",
    ]
    readable = 0
    for fn in key_files:
        fp = os.path.join(data_dir, fn)
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    json.load(f)
                readable += 1
            except Exception:
                pass
    checks["data_files_readable"] = readable
    checks["data_files_total"] = len(key_files)

    # Disk usage
    total_size = 0
    if os.path.isdir(data_dir):
        for dirpath, _dirnames, filenames in os.walk(data_dir):
            for fn in filenames:
                try:
                    total_size += os.path.getsize(os.path.join(dirpath, fn))
                except OSError:
                    pass
    checks["data_size_kb"] = round(total_size / 1024, 1)

    checks["status"] = "ok" if checks["data_dir_exists"] and checks["data_dir_writable"] else "degraded"
    checks["timestamp"] = datetime.now().isoformat()

    return checks


def render_health_page():
    """Render a minimal health-check page (for ?health=1).

    Call after st.set_page_config has already been invoked.
    """
    status = health_check()
    st.markdown("### 🩺 FinanceKit Health Check")
    st.json(status)
    st.stop()
