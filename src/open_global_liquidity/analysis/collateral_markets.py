"""Frozen-model collateral conditions versus subsequent Bitcoin outcomes."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats

from open_global_liquidity.analysis.bootstrap import moving_block_bootstrap_correlation


class CollateralMarketAnalysisError(ValueError):
    """Raised when collateral/Bitcoin validation inputs are unusable."""


PAIR_COLUMNS = [
    "signal_date",
    "signal_available_date",
    "model_id",
    "model_name",
    "collateral_conditions_score",
    "collateral_conditions_index",
    "collateral_regime",
    "market_id",
    "series_id",
    "provider",
    "availability_lag_months",
    "horizon_months",
    "start_observation_date",
    "start_value",
    "end_observation_date",
    "end_value",
    "market_return",
    "is_non_overlapping",
    "timing_classification",
    "classification",
]

SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "availability_lag_months",
    "horizon_months",
    "sample_policy",
    "observations",
    "correlation",
    "correlation_ci_lower",
    "correlation_ci_upper",
    "bootstrap_ci_lower",
    "bootstrap_ci_upper",
    "bootstrap_valid_resamples",
    "bootstrap_block_length",
    "bootstrap_seed",
    "mean_return",
    "median_return",
    "positive_share",
    "classification",
]


def build_collateral_bitcoin_pairs(
    collateral: pd.DataFrame,
    market_levels: pd.DataFrame,
    *,
    availability_lag_months: Sequence[int],
    forward_horizons_months: Sequence[int],
    max_market_staleness_days: int = 3,
) -> pd.DataFrame:
    """Pair the frozen monthly collateral score with strictly subsequent Bitcoin returns."""
    signal_columns = {
        "date",
        "collateral_conditions_score",
        "collateral_conditions_index",
        "collateral_regime",
        "model_name",
    }
    market_columns = {"date", "component", "series_id", "provider", "value"}
    if signal_columns - set(collateral.columns) or market_columns - set(market_levels.columns):
        raise CollateralMarketAnalysisError("Collateral or Bitcoin inputs are missing columns")
    lags = tuple(int(value) for value in availability_lag_months)
    horizons = tuple(int(value) for value in forward_horizons_months)
    if not lags or min(lags) < 0 or not horizons or min(horizons) < 1:
        raise CollateralMarketAnalysisError("Collateral validation lags or horizons are invalid")

    signals = collateral.dropna(subset=["collateral_conditions_score"]).copy()
    signals["date"] = pd.to_datetime(signals["date"]).dt.normalize().astype("datetime64[ns]")
    bitcoin = market_levels.loc[market_levels["component"] == "bitcoin"].copy()
    bitcoin["date"] = pd.to_datetime(bitcoin["date"]).dt.normalize().astype("datetime64[ns]")
    bitcoin["value"] = pd.to_numeric(bitcoin["value"], errors="coerce")
    bitcoin = bitcoin.dropna(subset=["date", "value"]).sort_values("date")
    if signals.empty or bitcoin.empty or (bitcoin["value"] <= 0).any():
        raise CollateralMarketAnalysisError(
            "Collateral scores and positive Bitcoin levels required"
        )
    metadata = bitcoin.iloc[-1]

    frames = []
    for lag in lags:
        for horizon in horizons:
            candidates = signals.copy()
            candidates["signal_date"] = candidates["date"]
            candidates["signal_available_date"] = candidates["date"] + pd.DateOffset(months=lag)
            candidates["end_target_date"] = candidates["signal_available_date"] + pd.DateOffset(
                months=horizon
            )
            candidates["signal_available_date"] = candidates["signal_available_date"].astype(
                "datetime64[ns]"
            )
            candidates["end_target_date"] = candidates["end_target_date"].astype("datetime64[ns]")
            for target, observed, value in (
                ("signal_available_date", "start_observation_date", "start_value"),
                ("end_target_date", "end_observation_date", "end_value"),
            ):
                candidates = pd.merge_asof(
                    candidates.sort_values(target),
                    bitcoin[["date", "value"]].rename(columns={"date": observed, "value": value}),
                    left_on=target,
                    right_on=observed,
                    direction="backward",
                )
            tolerance = pd.Timedelta(days=max_market_staleness_days)
            valid = (
                (
                    candidates["signal_available_date"] - candidates["start_observation_date"]
                    <= tolerance
                )
                & (candidates["end_target_date"] - candidates["end_observation_date"] <= tolerance)
                & candidates["start_value"].gt(0)
                & candidates["end_value"].gt(0)
            )
            candidates = candidates.loc[valid].copy()
            candidates["model_id"] = "collateral_conditions"
            candidates["market_id"] = "bitcoin"
            candidates["series_id"] = metadata["series_id"]
            candidates["provider"] = metadata["provider"]
            candidates["availability_lag_months"] = lag
            candidates["horizon_months"] = horizon
            candidates["market_return"] = candidates["end_value"] / candidates["start_value"] - 1
            candidates["is_non_overlapping"] = False
            candidates.loc[candidates.index[::horizon], "is_non_overlapping"] = True
            candidates["timing_classification"] = "model_assumption"
            candidates["classification"] = "statistical_transformation"
            frames.append(candidates)
    if not frames:
        raise CollateralMarketAnalysisError("No collateral and Bitcoin outcomes could be aligned")
    return pd.concat(frames, ignore_index=True)[PAIR_COLUMNS].sort_values(
        ["availability_lag_months", "horizon_months", "signal_date"], ignore_index=True
    )


def summarize_collateral_bitcoin_pairs(
    pairs: pd.DataFrame,
    *,
    overlapping_min_periods: int,
    non_overlapping_min_periods: int,
    confidence_level: float,
    bootstrap_resamples: int,
    bootstrap_block_length: int,
    bootstrap_seed: int,
) -> pd.DataFrame:
    """Report correlations and uncertainty without changing the frozen score parameters."""
    if set(PAIR_COLUMNS) - set(pairs.columns):
        raise CollateralMarketAnalysisError("Collateral Bitcoin pairs are missing columns")
    rows = []
    groups = ["model_id", "model_name", "market_id", "availability_lag_months", "horizon_months"]
    group_number = 0
    for policy in ("overlapping", "non_overlapping"):
        sample = pairs if policy == "overlapping" else pairs.loc[pairs["is_non_overlapping"]]
        minimum = (
            overlapping_min_periods if policy == "overlapping" else non_overlapping_min_periods
        )
        for keys, group in sample.groupby(groups, sort=True):
            valid = group.dropna(subset=["collateral_conditions_score", "market_return"])
            n = len(valid)
            correlation = (
                valid["collateral_conditions_score"].corr(valid["market_return"])
                if n >= minimum
                else math.nan
            )
            lower = upper = bootstrap_lower = bootstrap_upper = math.nan
            bootstrap_valid = 0
            if pd.notna(correlation):
                if n > 3 and abs(correlation) < 1:
                    z = np.arctanh(correlation)
                    critical = stats.norm.ppf((1 + confidence_level) / 2)
                    lower, upper = np.tanh(
                        [z - critical / np.sqrt(n - 3), z + critical / np.sqrt(n - 3)]
                    )
                else:
                    lower = upper = correlation
                bootstrap_lower, bootstrap_upper, bootstrap_valid = (
                    moving_block_bootstrap_correlation(
                        valid["collateral_conditions_score"],
                        valid["market_return"],
                        confidence_level=confidence_level,
                        resamples=bootstrap_resamples,
                        block_length=bootstrap_block_length,
                        seed=bootstrap_seed + group_number,
                    )
                )
            rows.append(
                {
                    **dict(zip(groups, keys, strict=True)),
                    "sample_policy": policy,
                    "observations": n,
                    "correlation": correlation,
                    "correlation_ci_lower": lower,
                    "correlation_ci_upper": upper,
                    "bootstrap_ci_lower": bootstrap_lower,
                    "bootstrap_ci_upper": bootstrap_upper,
                    "bootstrap_valid_resamples": bootstrap_valid,
                    "bootstrap_block_length": bootstrap_block_length,
                    "bootstrap_seed": bootstrap_seed + group_number,
                    "mean_return": valid["market_return"].mean(),
                    "median_return": valid["market_return"].median(),
                    "positive_share": valid["market_return"].gt(0).mean(),
                    "classification": "descriptive_statistic",
                }
            )
            group_number += 1
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS).sort_values(
        ["sample_policy", "availability_lag_months", "horizon_months"], ignore_index=True
    )
