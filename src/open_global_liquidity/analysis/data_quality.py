"""Transparent data-quality inventory without arbitrary cross-frequency scoring."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


def build_data_quality_inventory(snapshots: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Describe coverage and metadata availability for every public Parquet snapshot."""
    rows: list[dict[str, object]] = []
    for filename, frame in sorted(snapshots.items()):
        dates = (
            pd.to_datetime(frame["date"], errors="coerce").dropna()
            if "date" in frame.columns
            else pd.Series(dtype="datetime64[ns]")
        )
        retrievals = (
            pd.to_datetime(frame["retrieved_at"], errors="coerce", utc=True).dropna()
            if "retrieved_at" in frame.columns
            else pd.Series(dtype="datetime64[ns, UTC]")
        )
        if not dates.empty and not retrievals.empty:
            status = "observation_and_retrieval_metadata"
        elif not dates.empty:
            status = "observation_metadata_only"
        else:
            status = "structural_or_summary_table"
        rows.append(
            {
                "filename": filename,
                "rows": len(frame),
                "columns": len(frame.columns),
                "earliest_observation": dates.min() if not dates.empty else pd.NaT,
                "latest_observation": dates.max() if not dates.empty else pd.NaT,
                "latest_retrieval": retrievals.max() if not retrievals.empty else pd.NaT,
                "null_cells": int(frame.isna().sum().sum()),
                "duplicate_rows": int(frame.duplicated().sum()),
                "metadata_status": status,
                "classification": "data_quality_inventory",
            }
        )
    return pd.DataFrame(rows)
