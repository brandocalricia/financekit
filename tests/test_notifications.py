"""Tests for notification system."""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_create_notification(temp_data_dir):
    from utils.notifications import create_notification, get_notifications, get_unread_count

    create_notification("info", "test", "Test Title", "Test message")

    notifs = get_notifications()
    assert len(notifs) >= 1
    assert notifs[0]["title"] == "Test Title"
    assert notifs[0]["type"] == "info"
    assert notifs[0]["read"] is False


def test_unread_count(temp_data_dir):
    from utils.notifications import create_notification, get_unread_count

    create_notification("info", "test", "Notif 1", "Message 1")
    create_notification("warning", "test", "Notif 2", "Message 2")

    count = get_unread_count()
    assert count >= 2


def test_mark_read(temp_data_dir):
    from utils.notifications import create_notification, get_notifications, mark_read, get_unread_count

    create_notification("info", "test", "Read Test", "Will be read")
    notifs = get_notifications()
    notif_id = notifs[0]["id"]

    mark_read(notif_id)

    notifs_after = get_notifications()
    for n in notifs_after:
        if n["id"] == notif_id:
            assert n["read"] is True


def test_mark_all_read(temp_data_dir):
    from utils.notifications import create_notification, mark_all_read, get_unread_count

    create_notification("info", "test", "Notif A", "A")
    create_notification("info", "test", "Notif B", "B")
    mark_all_read()

    assert get_unread_count() == 0


def test_auto_cleanup(temp_data_dir):
    from utils.notifications import create_notification, clear_old, get_notifications
    from utils.data_persistence import load_json, save_json
    from datetime import datetime, timedelta

    # Create a notification and manually backdate it
    create_notification("info", "test", "Old Notif", "Old")
    notifs = load_json("notifications.json", default=[])
    old_date = (datetime.now() - timedelta(days=60)).isoformat()
    notifs[0]["timestamp"] = old_date
    save_json("notifications.json", notifs)

    clear_old(30)

    remaining = get_notifications()
    old_titles = [n["title"] for n in remaining if n["title"] == "Old Notif"]
    assert len(old_titles) == 0


def test_dedup(temp_data_dir):
    from utils.notifications import create_notification, get_notifications

    create_notification("info", "test", "Same Title", "Same msg", dedup_hours=24)
    create_notification("info", "test", "Same Title", "Same msg", dedup_hours=24)

    notifs = get_notifications()
    same_count = len([n for n in notifs if n["title"] == "Same Title"])
    assert same_count == 1


def test_notification_icon():
    from utils.notifications import notification_icon

    assert notification_icon("info") != ""
    assert notification_icon("warning") != ""
    assert notification_icon("success") != ""
    assert notification_icon("alert") != ""


def test_quiet_hours_suppression(temp_data_dir):
    """Notifications are suppressed during quiet hours (except urgent)."""
    from utils.notifications import create_notification
    from unittest.mock import patch

    with patch("utils.notifications._is_quiet_hours", return_value=True):
        # Normal priority suppressed
        result = create_notification("info", "test", "Quiet Test", "Should not appear")
        assert result is None
        # Urgent priority NOT suppressed
        result_urgent = create_notification("alert", "test", "Urgent Test", "Should appear", priority="urgent")
        assert result_urgent is not None


def test_rate_limiting(temp_data_dir):
    """Same type+module+title not duplicated within dedup window."""
    from utils.notifications import create_notification, get_notifications

    # Create 6 notifications from same module within rate limit
    for i in range(6):
        create_notification("info", "budget", f"Rate Test {i}", f"Message {i}", dedup_hours=0)
    # The 6th should be rate-limited (max 5 per module per hour for normal priority)
    notifs = get_notifications()
    budget_notifs = [n for n in notifs if n.get("module") == "budget"]
    assert len(budget_notifs) <= 5
