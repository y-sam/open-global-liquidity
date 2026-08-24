import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.provenance import (
    ProvenanceError,
    calculate_file_sha256,
    write_snapshot_manifest,
)


def test_manifest_records_hashes_dates_rows_and_source_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03", "2024-01-10"]),
            "provider": ["FRED", "FRED"],
            "series_id": ["WALCL", "WALCL"],
            "component": ["fed_assets", "fed_assets"],
            "value": [1.0, 2.0],
            "retrieved_at": [pd.Timestamp("2024-01-11", tz=UTC)] * 2,
        }
    )
    filename = "test_snapshot.parquet"
    path = tmp_path / filename
    frame.to_parquet(path, index=False)
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)

    manifest_path = write_snapshot_manifest(
        tmp_path,
        {filename: frame},
        project_root=tmp_path,
        pipeline_version="0.1.0",
        generated_at=datetime(2024, 1, 12, tzinfo=UTC),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["files"][filename]

    assert manifest["source_commit"] == "a" * 40
    assert manifest["working_tree_dirty"] is None
    assert manifest["snapshot_count"] == 1
    assert entry["rows"] == 2
    assert entry["earliest_observation"] == "2024-01-03"
    assert entry["latest_observation"] == "2024-01-10"
    assert entry["series_ids"] == ["WALCL"]
    assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_hash_fails_clearly_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ProvenanceError, match="does not exist"):
        calculate_file_sha256(tmp_path / "missing.parquet")
