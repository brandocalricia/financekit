"""Tests for data persistence — save, load, backup, recovery."""
import json
import os
import pytest


def test_save_load_roundtrip(temp_data_dir):
    from utils.data_persistence import save_json, load_json

    data = {"name": "test", "items": [1, 2, 3]}
    save_json("test.json", data)
    loaded = load_json("test.json")
    assert loaded["name"] == "test"
    assert loaded["items"] == [1, 2, 3]


def test_empty_file_handling(temp_data_dir):
    from utils.data_persistence import load_json

    result = load_json("nonexistent.json", default={"empty": True})
    assert result == {"empty": True}


def test_empty_file_default_list(temp_data_dir):
    from utils.data_persistence import load_json

    result = load_json("nonexistent.json")
    assert result == []


def test_backup_creation(temp_data_dir):
    from utils.data_persistence import save_json
    import time

    for i in range(3):
        save_json("backup_test.json", {"version": i})
        time.sleep(0.05)

    backup_dir = os.path.join(temp_data_dir, "backups")
    backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_test")]
    # First save has no file to back up; subsequent saves create backups
    assert len(backups) >= 1


def test_backup_rotation(temp_data_dir):
    from utils.data_persistence import save_json, MAX_BACKUPS
    import time

    for i in range(MAX_BACKUPS + 3):
        save_json("rotation_test.json", {"version": i})
        time.sleep(0.05)  # Ensure different timestamps

    backup_dir = os.path.join(temp_data_dir, "backups")
    backups = [f for f in os.listdir(backup_dir) if f.startswith("rotation_test")]
    assert len(backups) <= MAX_BACKUPS


def test_corruption_recovery(temp_data_dir):
    from utils.data_persistence import save_json, load_json, _path

    # Save valid data (creates a backup)
    save_json("corrupt_test.json", {"valid": True})
    # Save again (now there's a backup of the valid data)
    save_json("corrupt_test.json", {"valid": True, "version": 2})

    # Corrupt the main file
    fp = _path("corrupt_test.json")
    with open(fp, "w") as f:
        f.write("{broken json!!!")

    # Load should recover from backup
    result = load_json("corrupt_test.json", default={"fallback": True})
    assert isinstance(result, dict)
    assert result.get("valid") is True


def test_user_context_isolation(temp_data_dir):
    from utils.data_persistence import save_json, load_json, set_user_context, clear_user_context

    # Save as user A
    set_user_context("user_a")
    save_json("isolation.json", {"user": "A"})

    # Save as user B
    set_user_context("user_b")
    save_json("isolation.json", {"user": "B"})

    # Verify isolation
    set_user_context("user_a")
    assert load_json("isolation.json")["user"] == "A"

    set_user_context("user_b")
    assert load_json("isolation.json")["user"] == "B"

    clear_user_context()


def test_atomic_write_safety(temp_data_dir):
    from utils.data_persistence import save_json, load_json

    # Write initial data
    save_json("atomic.json", {"original": True})

    # Write new data
    save_json("atomic.json", {"updated": True})

    # No .tmp file should remain
    from utils.data_persistence import _path
    assert not os.path.exists(_path("atomic.json") + ".tmp")

    # Data should be the latest
    result = load_json("atomic.json")
    assert result.get("updated") is True
