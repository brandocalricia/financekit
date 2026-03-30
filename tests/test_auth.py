"""Tests for authentication system."""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def auth_dir(tmp_path, monkeypatch):
    """Redirect auth config to temp directory."""
    import utils.auth as auth_mod
    auth_file = str(tmp_path / "auth_config.json")
    users_file = str(tmp_path / "users.json")
    monkeypatch.setattr(auth_mod, "_AUTH_CONFIG_FILE", auth_file)
    monkeypatch.setattr(auth_mod, "_USERS_FILE", users_file)
    # Also need base data dir for user directories
    monkeypatch.setattr(auth_mod, "_BASE_DATA_DIR", str(tmp_path))
    return tmp_path


def test_register_user(auth_dir):
    from utils.auth import register_user, get_user_count

    success, msg = register_user("test@example.com", "password123", "Test User")
    assert success is True
    assert get_user_count() == 1


def test_login_success(auth_dir):
    from utils.auth import register_user, login_user

    register_user("login@example.com", "securepass", "Login User")
    success, result = login_user("login@example.com", "securepass")
    assert success is True
    assert result["email"] == "login@example.com"


def test_login_failure(auth_dir):
    from utils.auth import register_user, login_user

    register_user("fail@example.com", "correctpass", "Fail User")
    success, result = login_user("fail@example.com", "wrongpass")
    assert success is False


def test_duplicate_email(auth_dir):
    from utils.auth import register_user

    register_user("dup@example.com", "pass123456", "User 1")
    success, msg = register_user("dup@example.com", "pass654321", "User 2")
    assert success is False
    assert "exists" in msg.lower() or "already" in msg.lower()


def test_password_hash_security(auth_dir):
    from utils.auth import register_user

    register_user("hash@example.com", "mypassword", "Hash User")

    # Read the users file directly
    users_file = os.path.join(str(auth_dir), "users.json")
    with open(users_file, "r") as f:
        users_data = json.load(f)

    users = users_data.get("users", users_data)
    for user in users:
        if user.get("email") == "hash@example.com":
            pw_hash = user.get("password_hash", "")
            assert pw_hash != "mypassword"
            # Should be bcrypt ($2b$) or sha256$salt$hash
            assert "$" in pw_hash
            break


def test_session_token_create_validate(auth_dir):
    """Create a session token and validate it returns user info."""
    from utils.auth import create_session_token, validate_session_token
    import utils.auth as auth_mod

    # Redirect sessions file to temp dir
    sessions_file = os.path.join(str(auth_dir), "sessions.json")
    auth_mod._SESSIONS_FILE = sessions_file

    token = create_session_token("user1", "user1@example.com", "User One")
    assert token  # non-empty string

    result = validate_session_token(token)
    assert result is not None
    assert result["user_id"] == "user1"
    assert result["email"] == "user1@example.com"
    assert result["name"] == "User One"


def test_session_token_expiry(auth_dir):
    """Expired token should return None on validation."""
    from utils.auth import create_session_token, validate_session_token, _load_sessions, _save_sessions
    from datetime import datetime, timedelta
    import utils.auth as auth_mod

    sessions_file = os.path.join(str(auth_dir), "sessions.json")
    auth_mod._SESSIONS_FILE = sessions_file

    token = create_session_token("user2", "user2@example.com", "User Two")

    # Manually expire the token
    sessions = _load_sessions()
    for s in sessions["sessions"]:
        s["expiry"] = (datetime.now() - timedelta(hours=1)).isoformat()
    _save_sessions(sessions)

    result = validate_session_token(token)
    assert result is None


def test_session_token_revoke(auth_dir):
    """Revoked token should return None on validation."""
    from utils.auth import create_session_token, validate_session_token, revoke_session_token
    import utils.auth as auth_mod

    sessions_file = os.path.join(str(auth_dir), "sessions.json")
    auth_mod._SESSIONS_FILE = sessions_file

    token = create_session_token("user3", "user3@example.com", "User Three")
    assert validate_session_token(token) is not None

    revoke_session_token(token)
    assert validate_session_token(token) is None


def test_password_strength():
    """Test weak/medium/strong password ratings."""
    from utils.auth import password_strength

    assert password_strength("short") == "weak"
    assert password_strength("abcd123") == "weak"       # <8 chars
    assert password_strength("abcdef12") == "medium"     # 8+ chars, 2 types
    assert password_strength("Abcdef12") == "medium"     # 8 chars, 3 types but <12
    assert password_strength("Abcdef12!xyz") == "strong" # 12+ chars, 4 types
