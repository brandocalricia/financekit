import json
import os
import shutil
import time
import glob as _glob

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
MAX_BACKUPS = 5

# Per-user data isolation
_user_data_dir: str | None = None


def set_user_context(user_id: str):
    """Set the data directory to a user-specific path for per-user isolation."""
    global _user_data_dir
    _user_data_dir = os.path.join(DATA_DIR, "users", user_id)
    os.makedirs(_user_data_dir, exist_ok=True)
    os.makedirs(os.path.join(_user_data_dir, "backups"), exist_ok=True)


def clear_user_context():
    """Reset data directory to the default shared path."""
    global _user_data_dir
    _user_data_dir = None


def _get_data_dir() -> str:
    """Return the active data directory (user-specific or default)."""
    return _user_data_dir if _user_data_dir else DATA_DIR


def _get_backup_dir() -> str:
    """Return the active backup directory."""
    if _user_data_dir:
        return os.path.join(_user_data_dir, "backups")
    return BACKUP_DIR


def _path(filename: str) -> str:
    d = _get_data_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, filename)


def _backup(filepath: str):
    """Create a timestamped backup of a file. Keep last MAX_BACKUPS per file."""
    if not os.path.exists(filepath):
        return
    backup_dir = _get_backup_dir()
    os.makedirs(backup_dir, exist_ok=True)
    base = os.path.basename(filepath)
    name, ext = os.path.splitext(base)
    ts = int(time.time())
    backup_path = os.path.join(backup_dir, f"{name}.{ts}{ext}")
    try:
        shutil.copy2(filepath, backup_path)
    except OSError:
        return

    # Cleanup old backups for this file
    pattern = os.path.join(backup_dir, f"{name}.*{ext}")
    existing = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for old in existing[MAX_BACKUPS:]:
        try:
            os.remove(old)
        except OSError:
            pass


def _restore_from_backup(filename: str):
    """Try to restore a file from the most recent backup."""
    backup_dir = _get_backup_dir()
    name, ext = os.path.splitext(filename)
    pattern = os.path.join(backup_dir, f"{name}.*{ext}")
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
            data = json.load(f)
    except json.JSONDecodeError:
        # Try to restore from backup
        restored = _restore_from_backup(filename)
        if restored is not None:
            data = restored
        else:
            return default if default is not None else []
    except IOError:
        return default if default is not None else []

    # Validate and repair if schema exists
    try:
        from utils.validators import validate_and_repair
        data = validate_and_repair(filename, data)
    except Exception:
        pass  # Validation is best-effort — never block loading
    return data


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
