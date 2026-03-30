"""Sharing utilities for FinanceKit v5.5.

Generates share tokens, validates them, and provides read-only data access.
"""

import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from utils.data_persistence import load_json, save_json

SHARES_FILE = "shares.json"

# Expiry presets (in hours)
EXPIRY_OPTIONS = {
    "24 hours": 24,
    "7 days": 168,
    "30 days": 720,
    "Never": 0,
}


def _load_shares(user_id=None) -> list:
    """Load share tokens for a user."""
    return load_json(SHARES_FILE, default=[])


def _save_shares(shares: list, user_id=None):
    """Save share tokens."""
    save_json(SHARES_FILE, shares)


def create_share_link(
    user_name: str,
    modules: list[str] | None = None,
    expiry_hours: int = 168,
    password: str | None = None,
    share_type: str = "standard",
) -> dict:
    """Create a new share token.

    Args:
        user_name: Display name of the sharing user.
        modules: List of module keys to share, or None for all.
        expiry_hours: Hours until link expires (0 = never).
        password: Optional password protection.
        share_type: 'standard' or 'advisor'.

    Returns:
        Share record with token.
    """
    token = secrets.token_urlsafe(32)

    share = {
        "token": token,
        "user_name": user_name,
        "created": datetime.now().isoformat(),
        "expiry": (datetime.now() + timedelta(hours=expiry_hours)).isoformat() if expiry_hours > 0 else None,
        "modules": modules,  # None = all
        "password_hash": hashlib.sha256(password.encode()).hexdigest() if password else None,
        "share_type": share_type,
        "access_count": 0,
        "last_accessed": None,
        "active": True,
    }

    shares = _load_shares()
    shares.append(share)
    _save_shares(shares)

    return share


def validate_share_token(token: str, password: str | None = None) -> dict | None:
    """Validate a share token and return the share record if valid.

    Returns:
        Share record dict, or None if invalid/expired.
    """
    shares = _load_shares()

    for share in shares:
        if share.get("token") != token:
            continue
        if not share.get("active", True):
            return None

        # Check expiry
        expiry = share.get("expiry")
        if expiry:
            try:
                if datetime.fromisoformat(expiry) < datetime.now():
                    return None
            except Exception:
                pass

        # Check password
        if share.get("password_hash"):
            if not password:
                return {"needs_password": True, "token": token}
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            if pw_hash != share["password_hash"]:
                return {"wrong_password": True, "token": token}

        # Update access stats
        share["access_count"] = share.get("access_count", 0) + 1
        share["last_accessed"] = datetime.now().isoformat()
        _save_shares(shares)

        return share

    return None


def revoke_share(token: str):
    """Revoke (deactivate) a share link."""
    shares = _load_shares()
    for share in shares:
        if share.get("token") == token:
            share["active"] = False
            break
    _save_shares(shares)


def get_active_shares() -> list:
    """Get all active (non-expired, non-revoked) shares."""
    shares = _load_shares()
    now = datetime.now()
    active = []
    for share in shares:
        if not share.get("active", True):
            continue
        expiry = share.get("expiry")
        if expiry:
            try:
                if datetime.fromisoformat(expiry) < now:
                    continue
            except Exception:
                pass
        active.append(share)
    return active


def log_share_access(token: str, event: str):
    """Log an access event for audit purposes."""
    audit = load_json("share_audit.json", default=[])
    audit.append({
        "token": token[:8] + "...",
        "event": event,
        "timestamp": datetime.now().isoformat(),
    })
    # Keep last 100 entries
    save_json("share_audit.json", audit[-100:])
