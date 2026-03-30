"""Cloud data sync utilities for FinanceKit v5.3.

Enables syncing user data between desktop and cloud instances.
Uses the Streamlit Cloud instance as the canonical data store, with
timestamp-based conflict resolution (newest wins per file).
"""

import json
import os
import zipfile
import io
import time
from datetime import datetime

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Files to sync (user data, not system files)
SYNC_FILES = [
    "settings.json",
    "receipts.json",
    "portfolio.json",
    "budgets.json",
    "budget_transactions.json",
    "goals.json",
    "transactions.json",
    "statement_transactions.json",
    "manual_subscriptions.json",
    "cancelled_subscriptions.json",
    "sub_decisions.json",
    "sub_price_history.json",
    "sub_usage_notes.json",
    "freelance_data.json",
    "accounts.json",
    "liabilities.json",
    "net_worth_history.json",
]

SYNC_STATE_FILE = "sync_state.json"


def _get_user_data_dir(user_id=None):
    """Get the user-specific data directory."""
    if user_id:
        return os.path.join(_DATA_DIR, "users", user_id)
    return _DATA_DIR


def _load_sync_state(user_id=None):
    """Load sync state metadata."""
    data_dir = _get_user_data_dir(user_id)
    fp = os.path.join(data_dir, SYNC_STATE_FILE)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "enabled": False,
            "last_sync": None,
            "sync_frequency": "manual",
            "conflict_resolution": "newest",
            "file_timestamps": {},
        }


def _save_sync_state(state, user_id=None):
    """Save sync state metadata."""
    data_dir = _get_user_data_dir(user_id)
    os.makedirs(data_dir, exist_ok=True)
    fp = os.path.join(data_dir, SYNC_STATE_FILE)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def get_sync_status(user_id=None):
    """Get current sync status for display."""
    state = _load_sync_state(user_id)
    last_sync = state.get("last_sync")
    enabled = state.get("enabled", False)

    if not enabled:
        return {"status": "disabled", "icon": "", "label": "Cloud Sync is off. Enable it to back up your data across devices."}

    if not last_sync:
        return {"status": "never", "icon": "", "label": "Cloud Sync is enabled. Export a bundle to create your first backup."}

    # Calculate time since last sync
    try:
        last_dt = datetime.fromisoformat(last_sync)
        delta = datetime.now() - last_dt
        minutes = int(delta.total_seconds() / 60)

        if minutes < 1:
            ago = "just now"
        elif minutes < 60:
            ago = f"{minutes}m ago"
        elif minutes < 1440:
            ago = f"{minutes // 60}h ago"
        else:
            ago = f"{minutes // 1440}d ago"

        return {"status": "synced", "icon": "", "label": f"Last synced: {ago}"}
    except Exception:
        return {"status": "synced", "icon": "", "label": "Synced"}


def get_file_timestamps(user_id=None):
    """Get modification timestamps for all sync-eligible files."""
    data_dir = _get_user_data_dir(user_id)
    timestamps = {}
    for filename in SYNC_FILES:
        fp = os.path.join(data_dir, filename)
        if os.path.exists(fp):
            timestamps[filename] = os.path.getmtime(fp)
    return timestamps


def create_sync_bundle(user_id=None):
    """Create a ZIP bundle of all user data files for syncing.

    Returns:
        bytes: ZIP file contents, or None if no data.
    """
    data_dir = _get_user_data_dir(user_id)
    buf = io.BytesIO()
    file_count = 0

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include file metadata
        meta = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "files": {},
        }

        for filename in SYNC_FILES:
            fp = os.path.join(data_dir, filename)
            if os.path.exists(fp):
                try:
                    zf.write(fp, filename)
                    meta["files"][filename] = {
                        "mtime": os.path.getmtime(fp),
                        "size": os.path.getsize(fp),
                    }
                    file_count += 1
                except Exception:
                    continue

        # Write metadata
        zf.writestr("_sync_meta.json", json.dumps(meta, indent=2, default=str))

    if file_count == 0:
        return None

    return buf.getvalue()


def apply_sync_bundle(bundle_bytes, user_id=None, conflict_mode="newest"):
    """Apply a sync bundle to the local data directory.

    Args:
        bundle_bytes: ZIP file contents.
        user_id: User ID for data isolation.
        conflict_mode: 'newest' (default), 'cloud', 'local'.

    Returns:
        dict with 'updated', 'skipped', 'conflicts' lists.
    """
    data_dir = _get_user_data_dir(user_id)
    os.makedirs(data_dir, exist_ok=True)

    result = {"updated": [], "skipped": [], "conflicts": []}

    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as zf:
        # Read metadata
        try:
            meta = json.loads(zf.read("_sync_meta.json"))
        except Exception:
            meta = {"files": {}}

        for filename in SYNC_FILES:
            if filename not in zf.namelist():
                continue

            local_path = os.path.join(data_dir, filename)
            remote_meta = meta.get("files", {}).get(filename, {})
            remote_mtime = remote_meta.get("mtime", 0)

            # Check for conflicts
            if os.path.exists(local_path):
                local_mtime = os.path.getmtime(local_path)

                if conflict_mode == "local":
                    result["skipped"].append(filename)
                    continue
                elif conflict_mode == "cloud":
                    pass  # Always overwrite with cloud version
                else:  # newest wins
                    if local_mtime > remote_mtime:
                        result["skipped"].append(filename)
                        continue
                    elif abs(local_mtime - remote_mtime) < 1:
                        result["skipped"].append(filename)
                        continue
                    else:
                        result["conflicts"].append(filename)

            # Extract the file
            try:
                zf.extract(filename, data_dir)
                result["updated"].append(filename)
            except Exception:
                result["skipped"].append(filename)

    # Update sync state
    state = _load_sync_state(user_id)
    state["last_sync"] = datetime.now().isoformat()
    state["file_timestamps"] = get_file_timestamps(user_id)
    _save_sync_state(state, user_id)

    return result


def enable_sync(user_id=None, frequency="manual"):
    """Enable cloud sync."""
    state = _load_sync_state(user_id)
    state["enabled"] = True
    state["sync_frequency"] = frequency
    _save_sync_state(state, user_id)


def disable_sync(user_id=None):
    """Disable cloud sync."""
    state = _load_sync_state(user_id)
    state["enabled"] = False
    _save_sync_state(state, user_id)


def is_sync_enabled(user_id=None):
    """Check if sync is enabled."""
    state = _load_sync_state(user_id)
    return state.get("enabled", False)


def get_sync_frequency(user_id=None):
    """Get the sync frequency setting."""
    state = _load_sync_state(user_id)
    return state.get("sync_frequency", "manual")


def should_auto_sync(user_id=None):
    """Check if an auto-sync should trigger based on frequency setting."""
    state = _load_sync_state(user_id)
    if not state.get("enabled"):
        return False

    freq = state.get("sync_frequency", "manual")
    if freq == "manual":
        return False

    last_sync = state.get("last_sync")
    if not last_sync:
        return True

    try:
        last_dt = datetime.fromisoformat(last_sync)
        delta = (datetime.now() - last_dt).total_seconds() / 60

        freq_minutes = {"5min": 5, "15min": 15, "30min": 30, "60min": 60}
        threshold = freq_minutes.get(freq, 9999)
        return delta >= threshold
    except Exception:
        return True


def get_last_sync_time(user_id=None):
    """Return ISO timestamp of last successful sync, or None."""
    state = _load_sync_state(user_id)
    return state.get("last_sync")


def mark_synced(user_id=None):
    """Mark the current time as last sync time."""
    state = _load_sync_state(user_id)
    state["last_sync"] = datetime.now().isoformat()
    state["file_timestamps"] = get_file_timestamps(user_id)
    _save_sync_state(state, user_id)
