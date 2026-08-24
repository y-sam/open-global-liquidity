"""Descriptive correlation tools for liquidity-versus-market comparisons."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from open_global_liquidity.analysis.bootstrap import moving_block_bootstrap_correlation
from open_global_liquidity.analysis.lead_lag import MarketAnalysisError

GROUP_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "horizon_weeks",
    "return_type",
    "analysis_mode",
]


def calculate_lagged_correlations(
    comparisons: pd.DataFrame,
    *,
    min_periods: int = 52,
    sample_policy: str = "overlapping",
    confidence_level: float = 0.95,
    bootstrap_resamples: int = 1_000,
    bootstrap_block_length: int = 8,
    bootstrap_seed: int = 42,
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
    if not sample_policy:
        raise MarketAnalysisError("Correlation sample_policy cannot be empty")
    if not 0 < confidence_level < 1:
        raise MarketAnalysisError("Correlation confidence_level must be between 0 and 1")

    rows: list[dict[str, object]] = []
    for group_number, (keys, group) in enumerate(
        comparisons.groupby(GROUP_COLUMNS, sort=True, dropna=False)
    ):
        paired = group[["liquidity_signal", "market_return"]].dropna()
        correlation = (
            paired["liquidity_signal"].corr(paired["market_return"])
            if len(paired) >= min_periods
            else float("nan")
        )
        if len(paired) > 3 and pd.notna(correlation) and abs(correlation) < 1:
            fisher_z = np.arctanh(correlation)
            standard_error = 1 / np.sqrt(len(paired) - 3)
            critical = stats.norm.ppf((1 + confidence_level) / 2)
            correlation_ci_lower = np.tanh(fisher_z - critical * standard_error)
            correlation_ci_upper = np.tanh(fisher_z + critical * standard_error)
        elif pd.notna(correlation) and abs(correlation) == 1:
            correlation_ci_lower = correlation
            correlation_ci_upper = correlation
        else:
            correlation_ci_lower = float("nan")
            correlation_ci_upper = float("nan")
        if pd.notna(correlation):
            bootstrap_ci_lower, bootstrap_ci_upper, bootstrap_valid_resamples = (
                moving_block_bootstrap_correlation(
                    paired["liquidity_signal"],
                    paired["market_return"],
                    confidence_level=confidence_level,
                    resamples=bootstrap_resamples,
                    block_length=bootstrap_block_length,
                    seed=bootstrap_seed + group_number,
                )
            )
        else:
            bootstrap_ci_lower = float("nan")
            bootstrap_ci_upper = float("nan")
            bootstrap_valid_resamples = 0
        row = dict(zip(GROUP_COLUMNS, keys, strict=True))
        row.update(
            {
                "liquidity_signal_name": group["liquidity_signal_name"].iloc[0],
                "correlation": correlation,
                "observations": len(paired),
                "sample_policy": sample_policy,
                "confidence_level": confidence_level,
                "correlation_ci_lower": correlation_ci_lower,
                "correlation_ci_upper": correlation_ci_upper,
                "bootstrap_ci_lower": bootstrap_ci_lower,
                "bootstrap_ci_upper": bootstrap_ci_upper,
                "bootstrap_method": "circular_moving_block_percentile",
                "bootstrap_resamples": bootstrap_resamples,
                "bootstrap_valid_resamples": bootstrap_valid_resamples,
                "bootstrap_block_length": bootstrap_block_length,
                "bootstrap_seed": bootstrap_seed + group_number,
                "classification": "statistical_transformation",
            }
        )
        rows.append(row)
    columns = [
        *GROUP_COLUMNS,
        "liquidity_signal_name",
        "correlation",
        "observations",
        "sample_policy",
        "confidence_level",
        "correlation_ci_lower",
        "correlation_ci_upper",
        "bootstrap_ci_lower",
        "bootstrap_ci_upper",
        "bootstrap_method",
        "bootstrap_resamples",
        "bootstrap_valid_resamples",
        "bootstrap_block_length",
        "bootstrap_seed",
        "classification",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return (
        pd.DataFrame(rows)[columns]
        .sort_values(["model_id", "market_id", "analysis_mode", "horizon_weeks"])
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
