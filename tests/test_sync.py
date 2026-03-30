"""Tests for cloud sync utilities — bundle creation, auto-sync logic, mark_synced."""
import json
import os
import zipfile
import io
from datetime import datetime, timedelta

import pytest

import utils.data_persistence as dp


@pytest.fixture
def sync_data_dir(tmp_path, monkeypatch):
    """Redirect both data_persistence and sync module to a temp directory."""
    import utils.sync as sync_mod

    data_dir = str(tmp_path / "data")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "backups"), exist_ok=True)

    monkeypatch.setattr(dp, "DATA_DIR", data_dir)
    monkeypatch.setattr(dp, "BACKUP_DIR", os.path.join(data_dir, "backups"))
    monkeypatch.setattr(dp, "_user_data_dir", None)
    monkeypatch.setattr(sync_mod, "_DATA_DIR", data_dir)
    return data_dir


def test_create_sync_bundle(sync_data_dir):
    from utils.sync import create_sync_bundle, SYNC_FILES

    # Write a couple of data files into the temp data dir
    for name in ("settings.json", "portfolio.json"):
        with open(os.path.join(sync_data_dir, name), "w") as f:
            json.dump({name: True}, f)

    bundle = create_sync_bundle()
    assert bundle is not None

    # Verify it's a valid ZIP containing the files + metadata
    with zipfile.ZipFile(io.BytesIO(bundle), "r") as zf:
        names = zf.namelist()
        assert "settings.json" in names
        assert "portfolio.json" in names
        assert "_sync_meta.json" in names

        meta = json.loads(zf.read("_sync_meta.json"))
        assert "settings.json" in meta["files"]
        assert "portfolio.json" in meta["files"]


def test_create_sync_bundle_empty(sync_data_dir):
    """Returns None when there are no data files to bundle."""
    from utils.sync import create_sync_bundle

    result = create_sync_bundle()
    assert result is None


def test_should_auto_sync(sync_data_dir, monkeypatch):
    from utils.sync import should_auto_sync, _save_sync_state

    # Disabled sync -> never auto-sync
    _save_sync_state({"enabled": False, "sync_frequency": "5min", "last_sync": None})
    assert should_auto_sync() is False

    # Manual frequency -> never auto-sync even if enabled
    _save_sync_state({"enabled": True, "sync_frequency": "manual", "last_sync": None})
    assert should_auto_sync() is False

    # Enabled + frequency set + never synced -> should sync
    _save_sync_state({"enabled": True, "sync_frequency": "5min", "last_sync": None})
    assert should_auto_sync() is True

    # Synced recently (now) -> should NOT sync
    _save_sync_state({
        "enabled": True,
        "sync_frequency": "5min",
        "last_sync": datetime.now().isoformat(),
    })
    assert should_auto_sync() is False

    # Synced long ago -> should sync
    old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
    _save_sync_state({
        "enabled": True,
        "sync_frequency": "5min",
        "last_sync": old_time,
    })
    assert should_auto_sync() is True


def test_mark_synced(sync_data_dir):
    from utils.sync import mark_synced, get_last_sync_time

    assert get_last_sync_time() is None

    mark_synced()

    ts = get_last_sync_time()
    assert ts is not None
    # Timestamp should be very recent (within the last few seconds)
    dt = datetime.fromisoformat(ts)
    assert (datetime.now() - dt).total_seconds() < 5
