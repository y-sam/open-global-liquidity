"""Predeclared subperiod diagnostics for liquidity-versus-market relationships."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from open_global_liquidity.analysis.correlations import calculate_lagged_correlations
from open_global_liquidity.analysis.diagnostics import select_non_overlapping_returns
from open_global_liquidity.analysis.lead_lag import MarketAnalysisError
from open_global_liquidity.config import MarketResearchSubperiod


def calculate_subperiod_correlations(
    comparisons: pd.DataFrame,
    periods: Iterable[MarketResearchSubperiod],
    *,
    overlapping_min_periods: int,
    non_overlapping_min_periods: int,
    confidence_level: float,
) -> pd.DataFrame:
    """Calculate identical correlation diagnostics inside predeclared date partitions.

    Membership is based on the underlying liquidity observation date, not the assumed publication
    date or market outcome end date. Non-overlapping return windows are selected independently
    inside each period so a window cannot consume observations from a later partition.
    """
    if "signal_observation_date" not in comparisons.columns:
        raise MarketAnalysisError("Subperiod analysis requires signal_observation_date")
    period_list = tuple(periods)
    if not period_list:
        raise MarketAnalysisError("Subperiod analysis requires at least one configured period")

    signal_dates = pd.to_datetime(comparisons["signal_observation_date"], errors="coerce")
    frames: list[pd.DataFrame] = []
    for period_order, period in enumerate(period_list):
        mask = signal_dates >= pd.Timestamp(period.start)
        if period.end is not None:
            mask &= signal_dates <= pd.Timestamp(period.end)
        period_comparisons = comparisons.loc[mask].copy()
        sample_definitions = (
            ("overlapping", period_comparisons, overlapping_min_periods),
            (
                "non_overlapping",
                select_non_overlapping_returns(period_comparisons),
                non_overlapping_min_periods,
            ),
        )
        for sample_policy, sample, minimum in sample_definitions:
            result = calculate_lagged_correlations(
                sample,
                min_periods=minimum,
                sample_policy=sample_policy,
                confidence_level=confidence_level,
            )
            if result.empty:
                continue
            result["period_id"] = period.period_id
            result["period_label"] = period.label
            result["period_start"] = pd.Timestamp(period.start)
            result["period_end"] = pd.NaT if period.end is None else pd.Timestamp(period.end)
            result["period_order"] = period_order
            result["period_classification"] = "model_assumption"
            frames.append(result)

    if not frames:
        raise MarketAnalysisError("Configured subperiods contain no comparison observations")
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(
            [
                "period_order",
                "model_id",
                "market_id",
                "analysis_mode",
                "sample_policy",
                "horizon_weeks",
            ]
        )
        .reset_index(drop=True)
    )
