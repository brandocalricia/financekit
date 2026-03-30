"""Activity logging for cross-module recent activity feed."""
import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Per-user support
_user_data_dir: str | None = None


def _get_data_dir() -> str:
    """Return active data directory (user-specific or default)."""
    from utils.data_persistence import _get_data_dir as dp_get
    return dp_get()


def _log_path() -> str:
    d = _get_data_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "activity_log.json")


def log_activity(action: str, module: str, description: str):
    """Log a user action to the activity feed.

    Args:
        action: Short action verb (e.g. "added", "created", "updated", "deleted").
        module: Module name (e.g. "budget_tracker", "receipt_scanner").
        description: Human-readable description shown in the feed.
    """
    fp = _log_path()
    try:
        with open(fp, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    entries.insert(0, {
        "action": action,
        "module": module,
        "description": description,
        "timestamp": datetime.now().isoformat(),
    })

    # Keep last 100 entries
    entries = entries[:100]

    with open(fp, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)


def get_recent(limit: int = 10) -> list[dict]:
    """Return the most recent activity entries."""
    fp = _log_path()
    try:
        with open(fp, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return entries[:limit]


MODULE_ICONS = {
    "budget_tracker": "",
    "goal_tracker": "",
    "receipt_scanner": "",
    "portfolio_tracker": "",
    "report_generator": "",
    "job_tracker": "",
    "subscription_auditor": "",
    "settings": "",
}


def format_activity(entry: dict) -> str:
    """Format an activity entry for display."""
    icon = MODULE_ICONS.get(entry.get("module", ""), "")
    desc = entry.get("description", "")
    ts = entry.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts)
        now = datetime.now()
        diff = now - dt
        if diff.total_seconds() < 60:
            ago = "just now"
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            ago = f"{mins}m ago"
        elif diff.total_seconds() < 86400:
            hrs = int(diff.total_seconds() / 3600)
            ago = f"{hrs}h ago"
        else:
            days = diff.days
            ago = f"{days}d ago"
    except (ValueError, TypeError):
        ago = ""
    return f"{icon} {desc} — {ago}"
