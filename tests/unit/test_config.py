"""Tests for lynx configuration."""
import os
from pathlib import Path

from lynx.config import config, ensure_data_dir, get_data_dir, reset_config


class TestConfig:
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Clear env var if set
        if "LYNX_DATA_DIR" in os.environ:
            del os.environ["LYNX_DATA_DIR"]

    def test_default_data_dir(self):
        """Default data dir should be ~/.lynx/"""
        assert get_data_dir() == Path.home() / ".lynx"

    def test_env_var_overrides_default(self, tmp_path):
        """LYNX_DATA_DIR env var should override default."""
        os.environ["LYNX_DATA_DIR"] = str(tmp_path)
        assert get_data_dir() == tmp_path

    def test_explicit_config_overrides_env(self, tmp_path):
        """Explicit config() should override env var."""
        env_path = tmp_path / "env"
        explicit_path = tmp_path / "explicit"
        os.environ["LYNX_DATA_DIR"] = str(env_path)
        config(data_dir=explicit_path)
        assert get_data_dir() == explicit_path

    def test_config_returns_current_state(self, tmp_path):
        """config() should return current configuration."""
        config(data_dir=tmp_path)
        result = config()
        assert result["data_dir"] == str(tmp_path)

    def test_ensure_data_dir_creates_directory(self, tmp_path):
        """ensure_data_dir should create the directory."""
        test_dir = tmp_path / "lynx_test"
        config(data_dir=test_dir)
        result = ensure_data_dir()
        assert result.exists()
        assert result == test_dir
