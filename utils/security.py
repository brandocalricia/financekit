"""Security utilities for FinanceKit v5.7.

Rate limiting, session management, audit logging, and input sanitization.
"""

import json
import os
import secrets
import hashlib
import html as _html
from datetime import datetime, timedelta

_BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_LOGIN_ATTEMPTS_FILE = os.path.join(_BASE_DATA_DIR, "login_attempts.json")

# Common passwords (top 100 — abbreviated for space)
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "shadow", "123123", "654321", "superman", "qazwsx",
    "michael", "football", "password1", "password123", "1234", "12345",
    "123456789", "1234567890", "000000", "111111", "121212", "123321",
    "666666", "696969", "7777777", "888888", "admin", "welcome", "login",
    "passw0rd", "starwars", "hello", "charlie", "donald", "love123",
}


# ── Rate Limiting ──────────────────────────────────────────────────────

def _load_attempts() -> dict:
    os.makedirs(_BASE_DATA_DIR, exist_ok=True)
    if not os.path.exists(_LOGIN_ATTEMPTS_FILE):
        return {}
    try:
        with open(_LOGIN_ATTEMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_attempts(data: dict):
    os.makedirs(_BASE_DATA_DIR, exist_ok=True)
    with open(_LOGIN_ATTEMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def record_failed_login(email: str) -> int:
    """Record a failed login attempt. Returns remaining attempts before lockout."""
    attempts = _load_attempts()
    key = email.lower().strip()

    if key not in attempts:
        attempts[key] = {"count": 0, "first_attempt": None, "locked_until": None}

    entry = attempts[key]

    # Check if lockout has expired
    if entry.get("locked_until"):
        try:
            if datetime.fromisoformat(entry["locked_until"]) < datetime.now():
                entry["count"] = 0
                entry["locked_until"] = None
        except Exception:
            pass

    entry["count"] = entry.get("count", 0) + 1
    if not entry.get("first_attempt"):
        entry["first_attempt"] = datetime.now().isoformat()

    # Check 15-minute window
    first = entry.get("first_attempt", "")
    try:
        if first and (datetime.now() - datetime.fromisoformat(first)) > timedelta(minutes=15):
            # Reset window
            entry["count"] = 1
            entry["first_attempt"] = datetime.now().isoformat()
    except Exception:
        pass

    # Lock after 5 attempts
    max_attempts = 5
    if entry["count"] >= max_attempts:
        entry["locked_until"] = (datetime.now() + timedelta(minutes=30)).isoformat()

    attempts[key] = entry
    _save_attempts(attempts)

    remaining = max(0, max_attempts - entry["count"])
    return remaining


def is_account_locked(email: str) -> tuple[bool, str]:
    """Check if an account is locked. Returns (is_locked, message)."""
    attempts = _load_attempts()
    key = email.lower().strip()
    entry = attempts.get(key, {})

    locked_until = entry.get("locked_until")
    if not locked_until:
        return False, ""

    try:
        lock_dt = datetime.fromisoformat(locked_until)
        if lock_dt > datetime.now():
            remaining_mins = int((lock_dt - datetime.now()).total_seconds() / 60)
            return True, f"Account locked. Try again in {remaining_mins} minute{'s' if remaining_mins != 1 else ''}."
        else:
            # Lock expired — clear it
            entry["count"] = 0
            entry["locked_until"] = None
            attempts[key] = entry
            _save_attempts(attempts)
            return False, ""
    except Exception:
        return False, ""


def clear_failed_attempts(email: str):
    """Clear failed login attempts on successful login."""
    attempts = _load_attempts()
    key = email.lower().strip()
    if key in attempts:
        del attempts[key]
        _save_attempts(attempts)


def get_remaining_attempts(email: str) -> int:
    """Get remaining login attempts before lockout."""
    attempts = _load_attempts()
    key = email.lower().strip()
    entry = attempts.get(key, {})
    count = entry.get("count", 0)
    return max(0, 5 - count)


# ── Password Security ─────────────────────────────────────────────────

def check_password_requirements(password: str) -> dict:
    """Check password against all requirements. Returns dict of requirement: bool."""
    return {
        "length": len(password) >= 8,
        "number": any(c.isdigit() for c in password),
        "upper_lower": any(c.isupper() for c in password) and any(c.islower() for c in password),
        "special": any(not c.isalnum() for c in password),
        "not_common": password.lower() not in COMMON_PASSWORDS,
    }


def password_meets_requirements(password: str) -> bool:
    """Check if password meets all requirements."""
    reqs = check_password_requirements(password)
    return all(reqs.values())


# ── Session Security ──────────────────────────────────────────────────

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(48)


def get_active_sessions(user_id: str) -> list:
    """Get active sessions for a user."""
    from utils.data_persistence import load_json
    return load_json("sessions.json", default=[])


def add_session(user_id: str, device_info: str = "Unknown") -> str:
    """Create a new session and return the token."""
    from utils.data_persistence import load_json, save_json
    sessions = load_json("sessions.json", default=[])
    token = generate_session_token()

    sessions.append({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "created": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "device": device_info,
        "active": True,
    })

    # Keep only last 10 sessions
    sessions = sessions[-10:]
    save_json("sessions.json", sessions)
    return token


def invalidate_other_sessions(current_token_hash: str):
    """Invalidate all sessions except the current one."""
    from utils.data_persistence import load_json, save_json
    sessions = load_json("sessions.json", default=[])
    for s in sessions:
        if s.get("token_hash") != current_token_hash:
            s["active"] = False
    save_json("sessions.json", sessions)


# ── Audit Logging ─────────────────────────────────────────────────────

def log_audit_event(user_id: str, event_type: str, details: str = ""):
    """Log a security-relevant event."""
    from utils.data_persistence import load_json, save_json
    audit = load_json("audit.json", default=[])

    audit.append({
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "details": details,
        "user_id": user_id[:20] if user_id else "",
    })

    # Keep last 500 entries
    if len(audit) > 500:
        audit = audit[-500:]

    save_json("audit.json", audit)


def get_audit_log(limit: int = 50) -> list:
    """Get recent audit log entries."""
    from utils.data_persistence import load_json
    audit = load_json("audit.json", default=[])
    return sorted(audit, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]


# ── Input Sanitization ────────────────────────────────────────────────

def sanitize_html(text: str) -> str:
    """Sanitize text that will be rendered as HTML to prevent XSS."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return _html.escape(text)


def sanitize_for_display(text: str) -> str:
    """Sanitize text for safe display in st.markdown(unsafe_allow_html=True)."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    # Remove script tags and event handlers
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\bon\w+\s*=', '', text, flags=re.IGNORECASE)
    return _html.escape(text)
