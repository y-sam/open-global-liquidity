"""Descriptive correlation tools for liquidity-versus-market comparisons."""

from __future__ import annotations

import pandas as pd

from open_global_liquidity.analysis.lead_lag import MarketAnalysisError

GROUP_COLUMNS = ["model_id", "model_name", "market_id", "series_id", "horizon_weeks", "return_type"]


def calculate_lagged_correlations(
    comparisons: pd.DataFrame,
    *,
    min_periods: int = 52,
) -> pd.DataFrame:
    """Calculate Pearson correlations between liquidity signals and market outcomes.

    The result is descriptive. It does not establish causation and is not used to fit OGLI
    parameters. Groups with insufficient paired observations return a missing correlation.
    """
    required = set(GROUP_COLUMNS) | {"liquidity_signal", "liquidity_signal_name", "market_return"}
    missing = sorted(required - set(comparisons.columns))
    if missing:
        raise MarketAnalysisError(f"Correlation data is missing columns: {', '.join(missing)}")
    if min_periods < 2:
        raise MarketAnalysisError("Correlation min_periods must be at least 2")

    rows: list[dict[str, object]] = []
    for keys, group in comparisons.groupby(GROUP_COLUMNS, sort=True, dropna=False):
        paired = group[["liquidity_signal", "market_return"]].dropna()
        correlation = (
            paired["liquidity_signal"].corr(paired["market_return"])
            if len(paired) >= min_periods
            else float("nan")
        )
        row = dict(zip(GROUP_COLUMNS, keys, strict=True))
        row.update(
            {
                "liquidity_signal_name": group["liquidity_signal_name"].iloc[0],
                "correlation": correlation,
                "observations": len(paired),
                "classification": "statistical_transformation",
            }
        )
        rows.append(row)
    return (
        pd.DataFrame(rows)
        .sort_values(["model_id", "market_id", "horizon_weeks"])
        .reset_index(drop=True)
    )


def add_rolling_correlations(
    comparisons: pd.DataFrame,
    *,
    window_weeks: int = 52,
    min_periods: int = 26,
) -> pd.DataFrame:
    """Add trailing Pearson correlations within each model, market, and horizon group."""
    required = set(GROUP_COLUMNS) | {"date", "liquidity_signal", "market_return"}
    missing = sorted(required - set(comparisons.columns))
    if missing:
        raise MarketAnalysisError(f"Rolling correlation data is missing: {', '.join(missing)}")
    if min_periods < 2 or window_weeks < min_periods:
        raise MarketAnalysisError("Rolling-correlation history settings are inconsistent")

    frames: list[pd.DataFrame] = []
    for _keys, group in comparisons.groupby(GROUP_COLUMNS, sort=True, dropna=False):
        group = group.sort_values("date").copy()
        group["rolling_correlation"] = (
            group["liquidity_signal"]
            .rolling(window_weeks, min_periods=min_periods)
            .corr(group["market_return"])
        )
        group["rolling_window_weeks"] = window_weeks
        group["rolling_min_periods"] = min_periods
        frames.append(group)
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["model_id", "market_id", "horizon_weeks", "date"])
        .reset_index(drop=True)
    )
