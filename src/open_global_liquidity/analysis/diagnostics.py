"""Robustness diagnostics for liquidity-versus-market research."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from open_global_liquidity.analysis.lead_lag import MarketAnalysisError

DIAGNOSTIC_GROUP_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "horizon_weeks",
    "return_type",
    "analysis_mode",
]


def select_non_overlapping_returns(comparisons: pd.DataFrame) -> pd.DataFrame:
    """Select chronologically non-overlapping outcome windows within each research group.

    The greedy rule keeps the earliest valid window, then accepts the next window whose start is
    on or after the prior window's end. Sharing an endpoint is allowed because the simple returns
    then cover adjacent, rather than overlapping, close-to-close intervals.
    """
    required = set(DIAGNOSTIC_GROUP_COLUMNS) | {
        "return_start_date",
        "return_end_date",
        "market_return",
    }
    missing = sorted(required - set(comparisons.columns))
    if missing:
        raise MarketAnalysisError(
            "Non-overlapping return selection is missing: " + ", ".join(missing)
        )

    frames: list[pd.DataFrame] = []
    for _keys, group in comparisons.groupby(DIAGNOSTIC_GROUP_COLUMNS, sort=True, dropna=False):
        candidates = group.dropna(
            subset=["market_return", "return_start_date", "return_end_date"]
        ).sort_values(["return_start_date", "return_end_date"])
        selected_indices: list[object] = []
        previous_end: pd.Timestamp | None = None
        for row in candidates.itertuples():
            start = pd.Timestamp(row.return_start_date)
            end = pd.Timestamp(row.return_end_date)
            if previous_end is None or start >= previous_end:
                selected_indices.append(row.Index)
                previous_end = end
        frames.append(group.loc[selected_indices].copy())

    if not frames:
        return comparisons.iloc[0:0].copy()
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values([*DIAGNOSTIC_GROUP_COLUMNS, "date"])
        .reset_index(drop=True)
    )


def calculate_regime_return_statistics(
    comparisons: pd.DataFrame,
    *,
    sample_policy: str,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """Summarize Bitcoin outcomes by the OGLI regime known at the signal date.

    Confidence intervals use the classical Student-t interval for the arithmetic mean. They are
    descriptive uncertainty estimates, not forecast intervals; the non-overlapping sample is the
    preferred robustness view for positive forward horizons.
    """
    required = set(DIAGNOSTIC_GROUP_COLUMNS) | {"regime", "market_return"}
    missing = sorted(required - set(comparisons.columns))
    if missing:
        raise MarketAnalysisError("Regime analysis is missing columns: " + ", ".join(missing))
    if not 0 < confidence_level < 1:
        raise MarketAnalysisError("Confidence level must be between 0 and 1")
    if not sample_policy:
        raise MarketAnalysisError("Sample policy cannot be empty")

    rows: list[dict[str, object]] = []
    group_columns = [*DIAGNOSTIC_GROUP_COLUMNS, "regime"]
    for keys, group in comparisons.groupby(group_columns, sort=True, dropna=False):
        values = group["market_return"].dropna().astype(float)
        observations = len(values)
        mean = values.mean() if observations else float("nan")
        median = values.median() if observations else float("nan")
        positive_share = (values > 0).mean() if observations else float("nan")
        standard_error = values.sem() if observations >= 2 else float("nan")
        if observations >= 2 and np.isfinite(standard_error):
            critical = stats.t.ppf((1 + confidence_level) / 2, df=observations - 1)
            margin = critical * standard_error
            lower, upper = mean - margin, mean + margin
        else:
            lower, upper = float("nan"), float("nan")
        row = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "sample_policy": sample_policy,
                "observations": observations,
                "mean_return": mean,
                "median_return": median,
                "positive_share": positive_share,
                "standard_error": standard_error,
                "confidence_level": confidence_level,
                "mean_ci_lower": lower,
                "mean_ci_upper": upper,
                "classification": "statistical_transformation",
            }
        )
        rows.append(row)
    columns = [
        *group_columns,
        "sample_policy",
        "observations",
        "mean_return",
        "median_return",
        "positive_share",
        "standard_error",
        "confidence_level",
        "mean_ci_lower",
        "mean_ci_upper",
        "classification",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)[columns].sort_values(group_columns).reset_index(drop=True)
