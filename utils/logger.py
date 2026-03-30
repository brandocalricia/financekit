"""Centralized logging for FinanceKit — rotating file handler with timing."""
import functools
import logging
import os
import time
from logging.handlers import RotatingFileHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "financekit.log")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

_logger = None


def get_logger(name: str = "financekit") -> logging.Logger:
    """Get or create the app-wide logger with rotating file handler."""
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(LOG_DIR, exist_ok=True)

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on re-import
    if not _logger.handlers:
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        _logger.addHandler(fh)

    return _logger


def timed(label: str = ""):
    """Decorator that logs execution time of a function at INFO level."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            tag = label or func.__name__
            get_logger().info(f"{tag} completed in {elapsed:.1f}ms")
            return result
        return wrapper
    return decorator


def read_log_lines(max_lines: int = 100, level_filter: str = "ALL") -> list[str]:
    """Read the last N log lines, optionally filtered by level."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except IOError:
        return []

    if level_filter and level_filter != "ALL":
        lines = [l for l in lines if f"[{level_filter}]" in l]

    return lines[-max_lines:]


def clear_logs():
    """Clear the log file."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except IOError:
        pass


def get_log_path() -> str:
    return LOG_FILE
