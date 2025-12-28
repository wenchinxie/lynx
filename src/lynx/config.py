"""Configuration management for lynx."""
import os
from pathlib import Path
from typing import Any

# Module-level configuration
_config: dict[str, Any] = {
    "data_dir": None,  # Will be set to default on first access
}


def get_data_dir() -> Path:
    """Get the data directory path.

    Priority:
    1. Explicitly set via config(data_dir=...)
    2. LYNX_DATA_DIR environment variable
    3. Default: ~/.lynx/
    """
    if _config["data_dir"] is not None:
        return Path(_config["data_dir"])

    env_dir = os.environ.get("LYNX_DATA_DIR")
    if env_dir:
        return Path(env_dir)

    return Path.home() / ".lynx"


def config(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Get or set global configuration.

    Args:
        data_dir: Override default data directory

    Returns:
        Current configuration dict

    Example:
        >>> lynx.config(data_dir="/custom/path")
        >>> lynx.config()  # Returns current config
    """
    if data_dir is not None:
        _config["data_dir"] = Path(data_dir)

    return {
        "data_dir": str(get_data_dir()),
    }


def reset_config() -> None:
    """Reset configuration to defaults (mainly for testing)."""
    _config["data_dir"] = None


def ensure_data_dir() -> Path:
    """Ensure the data directory exists and return its path."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
