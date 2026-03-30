"""Authentication system for FinanceKit — local email/password + OAuth stubs."""
import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta

_BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_USERS_FILE = os.path.join(_BASE_DATA_DIR, "users.json")
_AUTH_CONFIG_FILE = os.path.join(_BASE_DATA_DIR, "auth_config.json")

DEFAULT_AUTH_CONFIG = {
    "require_auth": True,
    "google": {"client_id": "", "client_secret": ""},
    "github": {"client_id": "", "client_secret": ""},
    "session_expiry_hours": 24,
}


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt if available, fallback to SHA-256 + salt."""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except ImportError:
        salt = secrets.token_hex(16)
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"sha256${salt}${h}"


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ImportError:
            return False
    elif password_hash.startswith("sha256$"):
        parts = password_hash.split("$")
        if len(parts) != 3:
            return False
        salt, stored_hash = parts[1], parts[2]
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return h == stored_hash
    return False


def _sanitize_user_id(email: str) -> str:
    """Convert email to a safe directory name."""
    return email.lower().replace("@", "_at_").replace(".", "_")


def load_auth_config() -> dict:
    """Load authentication configuration."""
    if not os.path.exists(_AUTH_CONFIG_FILE):
        return DEFAULT_AUTH_CONFIG.copy()
    try:
        with open(_AUTH_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Merge with defaults for any missing keys
        merged = DEFAULT_AUTH_CONFIG.copy()
        merged.update(cfg)
        return merged
    except Exception:
        return DEFAULT_AUTH_CONFIG.copy()


def save_auth_config(config: dict):
    """Save authentication configuration."""
    os.makedirs(_BASE_DATA_DIR, exist_ok=True)
    with open(_AUTH_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _load_users() -> dict:
    """Load user registry."""
    if not os.path.exists(_USERS_FILE):
        return {"users": []}
    try:
        with open(_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": []}


def _save_users(data: dict):
    """Save user registry."""
    os.makedirs(_BASE_DATA_DIR, exist_ok=True)
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def is_auth_required() -> bool:
    """Authentication is always required — free tier shows landing page."""
    return True


def get_google_credentials() -> tuple[str, str]:
    """Get Google OAuth client_id and client_secret.

    Checks Streamlit secrets first (for cloud deploy), then auth_config.json (local).
    Returns (client_id, client_secret) — both empty strings if not configured.
    """
    # 1. Streamlit secrets (cloud)
    try:
        import streamlit as _st
        sec = _st.secrets.get("google", {})
        cid = sec.get("client_id", "")
        csec = sec.get("client_secret", "")
        if cid and csec:
            return cid, csec
    except Exception:
        pass

    # 2. auth_config.json (local)
    cfg = load_auth_config()
    g = cfg.get("google", {})
    return g.get("client_id", ""), g.get("client_secret", "")


def get_google_redirect_uri() -> str:
    """Get Google OAuth redirect URI from secrets or config."""
    # 1. Streamlit secrets
    try:
        import streamlit as _st
        uri = _st.secrets.get("google", {}).get("redirect_uri", "")
        if uri:
            return uri
    except Exception:
        pass
    # 2. auth_config.json
    cfg = load_auth_config()
    return cfg.get("google", {}).get("redirect_uri", "")


def get_session_expiry_hours(remember_me: bool = False) -> int:
    """Get session expiry in hours."""
    if remember_me:
        return 720  # 30 days
    return load_auth_config().get("session_expiry_hours", 24)


def register_user(email: str, password: str, name: str = "") -> tuple[bool, str]:
    """Register a new local user. Returns (success, message)."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    users_data = _load_users()
    users = users_data.get("users", [])

    # Check for existing user
    if any(u["email"] == email for u in users):
        return False, "An account with this email already exists."

    user_id = _sanitize_user_id(email)
    new_user = {
        "id": user_id,
        "email": email,
        "name": name or email.split("@")[0],
        "password_hash": _hash_password(password),
        "auth_method": "local",
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
    }
    users.append(new_user)
    users_data["users"] = users
    _save_users(users_data)

    # Create user data directory
    _create_user_data_dir(user_id)

    return True, "Account created successfully!"


def login_user(email: str, password: str) -> tuple[bool, dict | str]:
    """Authenticate a local user. Returns (success, user_dict_or_error_message)."""
    email = email.strip().lower()
    users_data = _load_users()
    users = users_data.get("users", [])

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return False, "No account found with this email."

    if user.get("auth_method") != "local":
        return False, f"This account uses {user.get('auth_method', 'OAuth')} sign-in."

    if not _verify_password(password, user.get("password_hash", "")):
        return False, "Incorrect password."

    # Update last login
    user["last_login"] = datetime.now().isoformat()
    _save_users(users_data)

    return True, user


def login_oauth_user(email: str, name: str, auth_method: str) -> dict:
    """Login or create an OAuth user. Returns user dict."""
    email = email.strip().lower()
    users_data = _load_users()
    users = users_data.get("users", [])

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        # Auto-create account for OAuth users
        user_id = _sanitize_user_id(email)
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "password_hash": "",
            "auth_method": auth_method,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
        }
        users.append(user)
        _create_user_data_dir(user_id)
    else:
        user["last_login"] = datetime.now().isoformat()
        if name:
            user["name"] = name

    users_data["users"] = users
    _save_users(users_data)
    return user


def change_password(email: str, current_password: str, new_password: str) -> tuple[bool, str]:
    """Change password for a local user."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    users_data = _load_users()
    users = users_data.get("users", [])
    user = next((u for u in users if u["email"] == email.strip().lower()), None)

    if not user:
        return False, "User not found."
    if user.get("auth_method") != "local":
        return False, "Password change is only available for local accounts."
    if not _verify_password(current_password, user.get("password_hash", "")):
        return False, "Current password is incorrect."

    user["password_hash"] = _hash_password(new_password)
    _save_users(users_data)
    return True, "Password changed successfully!"


def delete_user(email: str) -> tuple[bool, str]:
    """Delete a user account and their data directory."""
    import shutil
    email = email.strip().lower()
    users_data = _load_users()
    users = users_data.get("users", [])

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return False, "User not found."

    user_id = user["id"]

    # Remove user data directory
    user_dir = os.path.join(_BASE_DATA_DIR, "users", user_id)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir, ignore_errors=True)

    # Remove from users list
    users_data["users"] = [u for u in users if u["email"] != email]
    _save_users(users_data)

    return True, "Account deleted."


def generate_reset_token(email: str) -> tuple[bool, str]:
    """Generate a password reset token. Returns (success, token_or_error)."""
    email = email.strip().lower()
    users_data = _load_users()
    user = next((u for u in users_data.get("users", []) if u["email"] == email), None)

    if not user:
        return False, "No account found with this email."
    if user.get("auth_method") != "local":
        return False, "Password reset is only available for local accounts."

    token = secrets.token_urlsafe(32)
    user["reset_token"] = token
    user["reset_expires"] = (datetime.now() + timedelta(hours=1)).isoformat()
    _save_users(users_data)
    return True, token


def reset_password_with_token(email: str, token: str, new_password: str) -> tuple[bool, str]:
    """Reset password using a token."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    email = email.strip().lower()
    users_data = _load_users()
    user = next((u for u in users_data.get("users", []) if u["email"] == email), None)

    if not user:
        return False, "User not found."
    if user.get("reset_token") != token:
        return False, "Invalid or expired reset token."

    try:
        expires = datetime.fromisoformat(user.get("reset_expires", ""))
        if datetime.now() > expires:
            return False, "Reset token has expired. Please request a new one."
    except Exception:
        return False, "Invalid reset token."

    user["password_hash"] = _hash_password(new_password)
    user.pop("reset_token", None)
    user.pop("reset_expires", None)
    _save_users(users_data)
    return True, "Password has been reset successfully!"


def password_strength(password: str) -> str:
    """Evaluate password strength. Returns 'weak', 'medium', or 'strong'."""
    if len(password) < 8:
        return "weak"
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    variety = sum([has_upper, has_lower, has_digit, has_special])
    if len(password) >= 12 and variety >= 3:
        return "strong"
    if len(password) >= 8 and variety >= 2:
        return "medium"
    return "weak"


def get_user_count() -> int:
    """Return the number of registered users."""
    return len(_load_users().get("users", []))


def get_user_data_dir(user_id: str) -> str:
    """Get the data directory path for a specific user."""
    return os.path.join(_BASE_DATA_DIR, "users", user_id)


def _create_user_data_dir(user_id: str):
    """Create a user's data directory with empty default JSON files."""
    user_dir = os.path.join(_BASE_DATA_DIR, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(os.path.join(user_dir, "backups"), exist_ok=True)

    # Create default empty data files
    defaults = {
        "budgets.json": {"budgets": {}},
        "goals.json": {"goals": []},
        "receipts.json": [],
        "portfolio.json": {"holdings": [], "alerts": [], "watchlist": []},
        "transactions.json": [],
        "freelance_data.json": {"clients": [], "invoices": []},
        "budget_transactions.json": [],
        "statement_transactions.json": [],
        "sub_decisions.json": {},
        "settings.json": {},
    }
    for fn, default_data in defaults.items():
        fp = os.path.join(user_dir, fn)
        if not os.path.exists(fp):
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)


def is_session_valid(login_time_iso: str, remember_me: bool = False) -> bool:
    """Check if the current session is still valid."""
    try:
        login_time = datetime.fromisoformat(login_time_iso)
        expiry_hours = get_session_expiry_hours(remember_me)
        return datetime.now() < login_time + timedelta(hours=expiry_hours)
    except Exception:
        return False


def session_hours_remaining(login_time_iso: str, remember_me: bool = False) -> float:
    """Return hours remaining in the current session, or 0 if expired."""
    try:
        login_time = datetime.fromisoformat(login_time_iso)
        expiry_hours = get_session_expiry_hours(remember_me)
        expiry_time = login_time + timedelta(hours=expiry_hours)
        remaining = (expiry_time - datetime.now()).total_seconds() / 3600
        return max(0, remaining)
    except Exception:
        return 0


def invalidate_all_sessions(email: str) -> tuple[bool, str]:
    """Invalidate all sessions for a user by updating a session_secret.

    Other sessions will fail validation when the secret doesn't match.
    """
    email = email.strip().lower()
    users_data = _load_users()
    user = next((u for u in users_data.get("users", []) if u["email"] == email), None)
    if not user:
        return False, "User not found."
    user["session_secret"] = secrets.token_hex(16)
    _save_users(users_data)
    return True, "All other sessions have been invalidated."
