"""Parquet storage for DataFrame artifacts."""

import shutil
from pathlib import Path

import pandas as pd


def get_artifacts_dir() -> Path:
    """Get the artifacts directory."""
    from lynx.config import get_data_dir

    return get_data_dir() / "artifacts"


def save_artifact(run_id: str, name: str, df: pd.DataFrame) -> str:
    """Save a DataFrame as Parquet. Returns relative file path."""
    artifact_dir = get_artifacts_dir() / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    file_path = artifact_dir / f"{name}.parquet"
    df.to_parquet(file_path, index=True)
    from lynx.config import get_data_dir

    return str(file_path.relative_to(get_data_dir()))


def load_artifact(file_path: str) -> pd.DataFrame:
    """Load a DataFrame from Parquet."""
    from lynx.config import get_data_dir

    full_path = get_data_dir() / file_path
    return pd.read_parquet(full_path)


def delete_artifacts(run_id: str) -> None:
    """Delete all artifacts for a run."""
    artifact_dir = get_artifacts_dir() / run_id
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
