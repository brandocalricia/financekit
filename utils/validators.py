"""JSON data schema validation and repair for FinanceKit."""
from utils.logger import get_logger

log = get_logger("validators")

# ── Schema definitions ─────────────────────────────────────────────────
# Each schema: {key: (type, default_value)}
# type can be: list, dict, str, int, float, bool

SCHEMAS = {
    "budgets.json": {
        "_schema_version": (int, 1),
        "categories": (dict, {}),
    },
    "goals.json": {
        "_type": "list",
        "_item_schema": {
            "id": (str, ""),
            "name": (str, ""),
            "target": (float, 0.0),
            "current": (float, 0.0),
            "deadline": (str, ""),
            "monthly": (float, 0.0),
            "history": (list, []),
        },
    },
    "portfolio.json": {
        "_schema_version": (int, 1),
        "holdings": (list, []),
        "alerts": (list, []),
        "watchlist": (list, []),
        "trade_history": (list, []),
    },
    "receipts.json": {
        "_type": "list",
        "_item_schema": {
            "id": (str, ""),
            "vendor": (str, "Unknown"),
            "date": (str, ""),
            "total": (float, 0.0),
            "category": (str, "Other"),
            "raw_text": (str, ""),
        },
    },
    "freelance_data.json": {
        "_schema_version": (int, 1),
        "clients": (list, []),
        "invoices": (list, []),
        "time_entries": (list, []),
        "recurring_invoices": (list, []),
        "expenses": (list, []),
    },
    "settings.json": {
        "_schema_version": (int, 1),
        "user_name": (str, ""),
        "user_email": (str, ""),
        "currency": (dict, {"code": "USD", "symbol": "$"}),
        "date_format": (str, "MM/DD/YYYY"),
        "theme": (str, "dark"),
        "enabled_modules": (list, ["budget", "goals", "receipts", "portfolio", "reports", "freelance", "subscriptions"]),
        "onboarding_complete": (bool, False),
    },
    "statement_transactions.json": {
        "_type": "list",
    },
    "sub_decisions.json": {
        "_type": "dict",
    },
    "notifications.json": {
        "_type": "list",
    },
    "liabilities.json": {
        "_type": "list",
    },
    "net_worth_history.json": {
        "_type": "list",
    },
    "manual_subscriptions.json": {
        "_type": "list",
    },
    "cancelled_subscriptions.json": {
        "_type": "list",
    },
    "budget_scenarios.json": {
        "_type": "list",
    },
    "accounts.json": {
        "_type": "list",
        "_item_schema": {
            "id": (str, ""),
            "name": (str, ""),
            "type": (str, "checking"),
            "institution": (str, ""),
            "last_four": (str, ""),
            "balance": (float, 0.0),
            "color": (str, "#6366f1"),
            "is_default": (bool, False),
            "created_at": (str, ""),
        },
    },
    "bills.json": {
        "_type": "list",
        "_item_schema": {
            "id": (str, ""),
            "name": (str, ""),
            "amount": (float, 0.0),
            "due_day": (int, 1),
            "frequency": (str, "monthly"),
            "category": (str, "Other"),
            "auto_pay": (bool, False),
            "last_paid": (str, ""),
            "notes": (str, ""),
            "active": (bool, True),
        },
    },
    "household.json": {
        "enabled": (bool, False),
        "name": (str, ""),
        "members": (list, []),
        "invite_code": (str, ""),
        "shared_budgets": (bool, True),
        "shared_goals": (bool, True),
    },
    "splits.json": {
        "_type": "list",
    },
}


def validate_and_repair(filename: str, data):
    """Validate data against schema and repair missing/broken fields.

    Returns the validated (possibly repaired) data.
    Never raises — always returns usable data.
    """
    schema = SCHEMAS.get(filename)
    if schema is None:
        return data  # No schema defined — pass through

    repairs = []

    # Handle list-type schemas
    if schema.get("_type") == "list":
        if not isinstance(data, list):
            log.warning(f"[{filename}] Expected list, got {type(data).__name__}. Resetting to [].")
            repairs.append(f"Reset to list (was {type(data).__name__})")
            data = []
        # Validate items if item schema defined
        item_schema = schema.get("_item_schema")
        if item_schema and data:
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    for key, (expected_type, default) in item_schema.items():
                        if key not in item:
                            item[key] = _copy_default(default)
                            repairs.append(f"Item {i}: added missing '{key}'")
                        elif not isinstance(item[key], expected_type):
                            item[key] = _coerce(item[key], expected_type, default)
                            repairs.append(f"Item {i}: coerced '{key}' to {expected_type.__name__}")
        if repairs:
            log.info(f"[{filename}] Repaired {len(repairs)} issues: {', '.join(repairs[:5])}")
        return data

    # Handle dict-only schemas (no field specs)
    if schema.get("_type") == "dict":
        if not isinstance(data, dict):
            log.warning(f"[{filename}] Expected dict, got {type(data).__name__}. Resetting to {{}}.")
            return {}
        return data

    # Handle dict-type schemas with field definitions
    if not isinstance(data, dict):
        log.warning(f"[{filename}] Expected dict, got {type(data).__name__}. Creating from defaults.")
        data = {}
        repairs.append(f"Reset to dict (was {type(data).__name__})")

    for key, (expected_type, default) in schema.items():
        if key.startswith("_"):
            # Internal schema keys
            if key == "_schema_version":
                if key not in data:
                    data[key] = default
                    repairs.append(f"Added {key}={default}")
            continue

        if key not in data:
            data[key] = _copy_default(default)
            repairs.append(f"Added missing '{key}' = {repr(default)[:30]}")
        elif not isinstance(data[key], expected_type):
            data[key] = _coerce(data[key], expected_type, default)
            repairs.append(f"Coerced '{key}' to {expected_type.__name__}")

    if repairs:
        log.info(f"[{filename}] Repaired {len(repairs)} issues: {', '.join(repairs[:5])}")

    return data


def _coerce(value, target_type, default):
    """Try to coerce a value to the target type."""
    try:
        if target_type == int:
            return int(float(value))
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return str(value)
        elif target_type == bool:
            return bool(value)
        elif target_type == list:
            if isinstance(value, (list, tuple)):
                return list(value)
            return _copy_default(default)
        elif target_type == dict:
            if isinstance(value, dict):
                return value
            return _copy_default(default)
    except (ValueError, TypeError):
        pass
    return _copy_default(default)


def _copy_default(default):
    """Return a copy of the default value to avoid mutation."""
    if isinstance(default, list):
        return list(default)
    if isinstance(default, dict):
        return dict(default)
    return default
