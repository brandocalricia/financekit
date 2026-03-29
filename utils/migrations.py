"""Data migration framework for FinanceKit.

Each data file has a _schema_version integer. Migrations are applied
in order to bring files up to the latest version.
"""
from utils.data_persistence import load_json, save_json
from utils.logger import get_logger

log = get_logger("migrations")


# ── Migration functions ────────────────────────────────────────────────
# Each takes (data) and returns modified data. Must be idempotent.

def _freelance_v0_to_v1(data):
    """Ensure freelance_data has all required keys."""
    if not isinstance(data, dict):
        data = {"clients": [], "invoices": []}
    for key in ("clients", "invoices", "time_entries", "recurring_invoices", "expenses"):
        if key not in data:
            data[key] = []
    data["_schema_version"] = 1
    return data


def _portfolio_v0_to_v1(data):
    """Ensure portfolio has all required keys and holdings have new fields."""
    if not isinstance(data, dict):
        data = {"holdings": [], "alerts": [], "watchlist": []}
    for key in ("holdings", "alerts", "watchlist", "trade_history"):
        if key not in data:
            data[key] = []
    # Ensure each holding has newer fields
    for h in data.get("holdings", []):
        if "dividend_yield" not in h:
            h["dividend_yield"] = 0
        if "sector" not in h:
            h["sector"] = "Auto"
    data["_schema_version"] = 1
    return data


def _settings_v0_to_v1(data):
    """Ensure settings has notifications and invoice sections."""
    if not isinstance(data, dict):
        data = {}
    if "notifications" not in data:
        data["notifications"] = {"enabled": True}
    if "invoice" not in data:
        data["invoice"] = {}
    data["_schema_version"] = 1
    return data


def _budgets_v0_to_v1(data):
    """Ensure budgets is a dict with categories."""
    if not isinstance(data, dict):
        data = {"categories": {}}
    if "categories" not in data:
        data["categories"] = {}
    data["_schema_version"] = 1
    return data


# ── Migration registry ─────────────────────────────────────────────────
# filename: [(from_version, to_version, migration_fn), ...]
MIGRATIONS = {
    "freelance_data.json": [
        (0, 1, _freelance_v0_to_v1),
    ],
    "portfolio.json": [
        (0, 1, _portfolio_v0_to_v1),
    ],
    "settings.json": [
        (0, 1, _settings_v0_to_v1),
    ],
    "budgets.json": [
        (0, 1, _budgets_v0_to_v1),
    ],
}

LATEST_VERSIONS = {
    "freelance_data.json": 1,
    "portfolio.json": 1,
    "settings.json": 1,
    "budgets.json": 1,
}


def get_schema_version(data) -> int:
    """Get the current schema version of a data dict."""
    if isinstance(data, dict):
        return data.get("_schema_version", 0)
    return 0


def run_migrations():
    """Run all pending migrations for all registered data files."""
    applied = []

    for filename, migration_list in MIGRATIONS.items():
        data = load_json(filename, default=None)
        if data is None:
            continue  # File doesn't exist yet

        current = get_schema_version(data)
        target = LATEST_VERSIONS.get(filename, 1)

        if current >= target:
            continue

        for from_v, to_v, fn in migration_list:
            if current == from_v:
                try:
                    data = fn(data)
                    current = to_v
                    log.info(f"Migration applied: {filename} v{from_v} -> v{to_v}")
                    applied.append(f"{filename} v{from_v}->v{to_v}")
                except Exception as e:
                    log.error(f"Migration failed: {filename} v{from_v} -> v{to_v}: {e}")
                    break

        if applied:
            save_json(filename, data)

    if applied:
        log.info(f"Migrations complete: {len(applied)} applied")
    return applied


def check_pending() -> list[str]:
    """Check which migrations are pending without applying them."""
    pending = []
    for filename in MIGRATIONS:
        data = load_json(filename, default=None)
        if data is None:
            continue
        current = get_schema_version(data)
        target = LATEST_VERSIONS.get(filename, 1)
        if current < target:
            pending.append(f"{filename}: v{current} -> v{target}")
    return pending
