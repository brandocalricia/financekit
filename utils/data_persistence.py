import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _path(filename: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)


def load_json(filename: str, default=None):
    fp = _path(filename)
    if not os.path.exists(fp):
        return default if default is not None else []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else []


def save_json(filename: str, data):
    fp = _path(filename)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
