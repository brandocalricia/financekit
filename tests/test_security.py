"""Tests for utils/security.py — rate limiting, password validation, audit logging, sanitization."""
import json
import os
import tempfile
from unittest.mock import patch
from datetime import datetime, timedelta

import pytest


# ── Rate Limiting ─────────────────────────────────────────────────────

class TestRateLimiting:
    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._attempts_file = os.path.join(self._tmp, "login_attempts.json")
        self._patches = [
            patch("utils.security._BASE_DATA_DIR", self._tmp),
            patch("utils.security._LOGIN_ATTEMPTS_FILE", self._attempts_file),
        ]
        for p in self._patches:
            p.start()

    def teardown_method(self):
        for p in self._patches:
            p.stop()
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_not_locked_initially(self):
        from utils.security import is_account_locked
        locked, msg = is_account_locked("test@example.com")
        assert not locked
        assert msg == ""

    def test_record_failed_login_decrements(self):
        from utils.security import record_failed_login
        remaining = record_failed_login("test@example.com")
        assert remaining == 4  # 5 max - 1 failure

    def test_locked_after_5_failures(self):
        from utils.security import record_failed_login, is_account_locked
        for _ in range(5):
            record_failed_login("test@example.com")
        locked, msg = is_account_locked("test@example.com")
        assert locked
        assert "locked" in msg.lower() or "minute" in msg.lower()

    def test_lockout_expires(self):
        from utils.security import record_failed_login, is_account_locked, _load_attempts, _save_attempts
        for _ in range(5):
            record_failed_login("test@example.com")
        # Manually set lock to the past
        attempts = _load_attempts()
        key = "test@example.com"
        attempts[key]["locked_until"] = (datetime.now() - timedelta(minutes=1)).isoformat()
        _save_attempts(attempts)
        locked, msg = is_account_locked("test@example.com")
        assert not locked

    def test_clear_failed_attempts(self):
        from utils.security import record_failed_login, clear_failed_attempts, get_remaining_attempts
        record_failed_login("test@example.com")
        record_failed_login("test@example.com")
        clear_failed_attempts("test@example.com")
        remaining = get_remaining_attempts("test@example.com")
        assert remaining == 5


# ── Password Requirements ────────────────────────────────────────────

class TestPasswordRequirements:
    def test_short_password_fails(self):
        from utils.security import check_password_requirements
        reqs = check_password_requirements("Ab1!")
        assert not reqs["length"]

    def test_no_number_fails(self):
        from utils.security import check_password_requirements
        reqs = check_password_requirements("Abcdefgh!")
        assert not reqs["number"]

    def test_no_upper_lower_fails(self):
        from utils.security import check_password_requirements
        reqs = check_password_requirements("abcdefg1!")
        assert not reqs["upper_lower"]

    def test_no_special_fails(self):
        from utils.security import check_password_requirements
        reqs = check_password_requirements("Abcdefg1")
        assert not reqs["special"]

    def test_common_password_fails(self):
        from utils.security import check_password_requirements
        reqs = check_password_requirements("password")
        assert not reqs["not_common"]

    def test_strong_password_passes_all(self):
        from utils.security import check_password_requirements, password_meets_requirements
        reqs = check_password_requirements("MyStr0ng!Pass")
        assert all(reqs.values())
        assert password_meets_requirements("MyStr0ng!Pass")


# ── Sanitization ─────────────────────────────────────────────────────

class TestSanitization:
    def test_sanitize_html_escapes_tags(self):
        from utils.security import sanitize_html
        result = sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_html_none(self):
        from utils.security import sanitize_html
        assert sanitize_html(None) == ""

    def test_sanitize_html_number(self):
        from utils.security import sanitize_html
        assert sanitize_html(42) == "42"

    def test_sanitize_for_display_strips_scripts(self):
        from utils.security import sanitize_for_display
        result = sanitize_for_display("<script>alert('x')</script>Hello")
        assert "script" not in result.lower() or "&lt;" in result
        # Should not contain executable script
        assert "<script>" not in result


# ── Audit Logging ────────────────────────────────────────────────────

class TestAuditLogging:
    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._user_dir = os.path.join(self._tmp, "users", "test_user")
        os.makedirs(self._user_dir, exist_ok=True)
        import utils.data_persistence as dp
        self._orig = dp._user_data_dir
        dp._user_data_dir = self._user_dir

    def teardown_method(self):
        import utils.data_persistence as dp
        dp._user_data_dir = self._orig
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_audit_log_records_event(self):
        from utils.security import log_audit_event, get_audit_log
        log_audit_event("test_user", "login_success", "Email: test@example.com")
        log = get_audit_log(limit=10)
        assert len(log) >= 1
        assert log[0]["event"] == "login_success"
        assert "test@example.com" in log[0]["details"]
