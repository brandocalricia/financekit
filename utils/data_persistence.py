import json
import os
import shutil
import time
import glob as _glob

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
MAX_BACKUPS = 5


def _path(filename: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)


def _backup(filepath: str):
    """Create a timestamped backup of a file. Keep last MAX_BACKUPS per file."""
    if not os.path.exists(filepath):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    base = os.path.basename(filepath)
    name, ext = os.path.splitext(base)
    ts = int(time.time())
    backup_path = os.path.join(BACKUP_DIR, f"{name}.{ts}{ext}")
    try:
        shutil.copy2(filepath, backup_path)
    except OSError:
        return

    # Cleanup old backups for this file
    pattern = os.path.join(BACKUP_DIR, f"{name}.*{ext}")
    existing = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for old in existing[MAX_BACKUPS:]:
        try:
            os.remove(old)
        except OSError:
            pass


def _restore_from_backup(filename: str):
    """Try to restore a file from the most recent backup."""
    name, ext = os.path.splitext(filename)
    pattern = os.path.join(BACKUP_DIR, f"{name}.*{ext}")
    backups = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for backup in backups:
        try:
            with open(backup, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Backup is valid JSON — restore it
            fp = _path(filename)
            shutil.copy2(backup, fp)
            return data
        except (json.JSONDecodeError, IOError):
            continue
    return None


def get_mtime(filename: str) -> float:
    """Get modification time of a data file. Returns 0 if file doesn't exist."""
    fp = _path(filename)
    try:
        return os.path.getmtime(fp)
    except OSError:
        return 0.0


def load_json(filename: str, default=None):
    fp = _path(filename)
    if not os.path.exists(fp):
        return default if default is not None else []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Try to restore from backup
        restored = _restore_from_backup(filename)
        if restored is not None:
            return restored
        return default if default is not None else []
    except IOError:
        return default if default is not None else []


def save_json(filename: str, data):
    fp = _path(filename)
    # Backup before overwriting
    _backup(fp)
    # Write atomically: write to temp file then rename
    tmp_path = fp + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        # Atomic rename (on Windows, need to remove target first)
        if os.path.exists(fp):
            os.replace(tmp_path, fp)
        else:
            os.rename(tmp_path, fp)
    except Exception:
        # If atomic write fails, try direct write
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
