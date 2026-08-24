"""Transparent comparisons between historical ALFRED vintages and current FRED values."""

from __future__ import annotations

import numpy as np
import pandas as pd

from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.fred import VINTAGE_COLUMNS


class RevisionAnalysisError(ValueError):
    """Raised when vintage and current frames cannot be compared safely."""


def compare_vintage_to_current(
    vintage: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    """Compare each as-of observation with today's current-vintage value.

    A nonzero revision can reflect a provider correction, methodological change, or other source
    update; this function does not infer why it changed. Missing current values remain explicit and
    are never filled from the vintage frame.
    """
    vintage_missing = sorted(set(VINTAGE_COLUMNS) - set(vintage.columns))
    current_missing = sorted(set(STANDARD_COLUMNS) - set(current.columns))
    if vintage_missing:
        raise RevisionAnalysisError("Vintage data is missing: " + ", ".join(vintage_missing))
    if current_missing:
        raise RevisionAnalysisError("Current data is missing: " + ", ".join(current_missing))
    if vintage.empty or current.empty:
        raise RevisionAnalysisError(
            "Revision comparison requires non-empty vintage and current data"
        )

    vintage_values = vintage.rename(
        columns={"value": "vintage_value", "retrieved_at": "vintage_retrieved_at"}
    )
    current_values = current.rename(
        columns={
            "date": "observation_date",
            "value": "current_value",
            "retrieved_at": "current_retrieved_at",
        }
    )
    keys = ["country", "series_id", "component", "observation_date", "unit", "frequency"]
    result = vintage_values.merge(
        current_values[[*keys, "current_value", "current_retrieved_at"]],
        on=keys,
        how="left",
        validate="one_to_one",
    )
    result["revision"] = result["current_value"] - result["vintage_value"]
    result["revision_pct"] = np.where(
        result["vintage_value"].notna() & result["vintage_value"].ne(0),
        result["revision"] / result["vintage_value"],
        np.nan,
    )
    result["revision_status"] = np.select(
        [
            result["current_value"].isna(),
            result["vintage_value"].isna(),
            result["revision"].eq(0),
        ],
        ["missing_current", "missing_vintage", "unchanged"],
        default="revised",
    )
    result["classification"] = "statistical_transformation"
    columns = [
        "observation_date",
        "vintage_date",
        "country",
        "series_id",
        "component",
        "unit",
        "frequency",
        "vintage_value",
        "current_value",
        "revision",
        "revision_pct",
        "revision_status",
        "realtime_start",
        "realtime_end",
        "vintage_retrieved_at",
        "current_retrieved_at",
        "classification",
    ]
    return result[columns].sort_values(["series_id", "observation_date"]).reset_index(drop=True)
