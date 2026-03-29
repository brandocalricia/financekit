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
