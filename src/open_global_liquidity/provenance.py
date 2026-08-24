"""Auditable metadata for published dashboard snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


class ProvenanceError(ValueError):
    """Raised when a reproducible snapshot manifest cannot be created or validated."""


def calculate_file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it entirely into memory."""
    if not path.is_file():
        raise ProvenanceError(f"Snapshot file does not exist: {path}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ProvenanceError(f"Could not hash snapshot file {path}: {exc}") from exc
    return digest.hexdigest()


def resolve_source_commit(project_root: Path) -> str:
    """Resolve the code commit used for a pipeline run, preferring GitHub's immutable SHA."""
    github_sha = os.environ.get("GITHUB_SHA", "").strip()
    if github_sha:
        return github_sha
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else "unavailable"


def resolve_working_tree_dirty(project_root: Path) -> bool | None:
    """Report whether uncommitted files mean the source commit is not a complete code identity."""
    try:
        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                ".",
                ":(exclude)data/reference",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _iso_timestamp(value: object) -> str | None:
    timestamp = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(timestamp):
        return None
    return pd.Timestamp(timestamp).isoformat()


def _snapshot_entry(path: Path, frame: pd.DataFrame) -> dict[str, object]:
    entry: dict[str, object] = {
        "sha256": calculate_file_sha256(path),
        "bytes": path.stat().st_size,
        "rows": len(frame),
        "columns": frame.columns.tolist(),
    }
    if "date" in frame.columns and frame["date"].notna().any():
        dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
        if not dates.empty:
            entry["earliest_observation"] = dates.min().date().isoformat()
            entry["latest_observation"] = dates.max().date().isoformat()
    if "retrieved_at" in frame.columns and frame["retrieved_at"].notna().any():
        entry["latest_retrieval"] = _iso_timestamp(frame["retrieved_at"].max())
    for column in ("provider", "series_id", "component", "model_id", "market_id"):
        if column in frame.columns:
            entry[column + "s"] = sorted(str(value) for value in frame[column].dropna().unique())
    return entry


def write_snapshot_manifest(
    snapshot_dir: Path,
    snapshots: Mapping[str, pd.DataFrame],
    *,
    project_root: Path,
    pipeline_version: str,
    generated_at: datetime | pd.Timestamp | None = None,
) -> Path:
    """Write deterministic JSON metadata for an already-published snapshot collection.

    The manifest distinguishes the generation timestamp from observation and retrieval dates. Its
    source commit identifies the exact code used to create the files, while each SHA-256 digest
    allows consumers to verify that the Parquet bytes have not changed.
    """
    if not snapshots:
        raise ProvenanceError("Cannot publish an empty snapshot manifest")
    generated = pd.Timestamp(generated_at if generated_at is not None else datetime.now(UTC))
    if generated.tzinfo is None:
        generated = generated.tz_localize(UTC)
    else:
        generated = generated.tz_convert(UTC)

    files: dict[str, dict[str, object]] = {}
    for filename, frame in sorted(snapshots.items()):
        files[filename] = _snapshot_entry(snapshot_dir / filename, frame)
    manifest = {
        "schema_version": 1,
        "classification": "snapshot_provenance",
        "generated_at": generated.isoformat(),
        "pipeline_version": pipeline_version,
        "source_commit": resolve_source_commit(project_root),
        "working_tree_dirty": resolve_working_tree_dirty(project_root),
        "snapshot_count": len(files),
        "files": files,
    }
    path = snapshot_dir / "dashboard_snapshot_manifest.json"
    try:
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ProvenanceError(f"Could not write snapshot manifest {path}: {exc}") from exc
    return path
