"""Tests for performance utilities (v5.9)."""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """Tests for the health_check function."""

    def test_health_check_returns_dict(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        result = perf.health_check()
        assert isinstance(result, dict)
        assert result["status"] in ("ok", "degraded")
        assert "timestamp" in result

    def test_health_check_data_dir_exists(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        result = perf.health_check()
        assert result["data_dir_exists"] is True
        assert result["data_dir_writable"] is True
        assert result["status"] == "ok"

    def test_health_check_missing_dir(self, tmp_path, monkeypatch):
        import utils.performance as perf
        monkeypatch.setattr(perf, "_DATA_DIR", str(tmp_path / "nonexistent"))

        result = perf.health_check()
        assert result["data_dir_exists"] is False
        assert result["status"] == "degraded"

    def test_health_check_valid_settings(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        settings_path = os.path.join(data_dir, "settings.json")
        with open(settings_path, "w") as f:
            json.dump({"theme": "dark"}, f)

        result = perf.health_check()
        assert result["settings_valid"] is True

    def test_health_check_corrupt_settings(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        settings_path = os.path.join(data_dir, "settings.json")
        with open(settings_path, "w") as f:
            f.write("{invalid json")

        result = perf.health_check()
        assert result["settings_valid"] is False

    def test_health_check_data_size(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        # Write a test file
        with open(os.path.join(data_dir, "test.json"), "w") as f:
            f.write("x" * 1024)

        result = perf.health_check()
        assert result["data_size_kb"] >= 1.0

    def test_health_check_readable_files(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        # Create some key data files
        for fn in ["budgets.json", "goals.json"]:
            with open(os.path.join(data_dir, fn), "w") as f:
                json.dump({}, f)

        result = perf.health_check()
        assert result["data_files_readable"] == 2
        assert result["data_files_total"] == 5


# ---------------------------------------------------------------------------
# smart_load_json
# ---------------------------------------------------------------------------

class TestSmartLoadJson:
    """Tests for the smart_load_json function."""

    def test_load_existing_file(self, tmp_path, monkeypatch):
        import utils.performance as perf
        # Clear any cached data
        perf.cached_load_json.clear()

        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        test_data = {"key": "value", "num": 42}
        with open(os.path.join(data_dir, "test.json"), "w") as f:
            json.dump(test_data, f)

        result = perf.smart_load_json("test.json")
        assert result == test_data

    def test_load_missing_file_returns_default(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        result = perf.smart_load_json("nonexistent.json", default=[])
        assert result == []

    def test_load_missing_file_default_none(self, tmp_path, monkeypatch):
        import utils.performance as perf
        data_dir = str(tmp_path / "data")
        os.makedirs(data_dir, exist_ok=True)
        monkeypatch.setattr(perf, "_DATA_DIR", data_dir)

        result = perf.smart_load_json("nonexistent.json")
        assert result is None


# ---------------------------------------------------------------------------
# paginate
# ---------------------------------------------------------------------------

class TestPaginate:
    """Tests for the paginate helper."""

    def test_small_list_returns_all(self):
        from utils.performance import paginate
        items = list(range(10))
        result = paginate(items, page_key="test_pg", page_size=50)
        assert result == items

    def test_empty_list(self):
        from utils.performance import paginate
        result = paginate([], page_key="test_pg2", page_size=50)
        assert result == []

    def test_none_items(self):
        from utils.performance import paginate
        result = paginate(None, page_key="test_pg3", page_size=50)
        assert result is None
