"""Current-vintage Global Model G versus subsequent Bitcoin outcomes."""

from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd


class GlobalMarketAnalysisError(ValueError):
    """Raised when the global signal and Bitcoin levels cannot be aligned safely."""


GLOBAL_MARKET_PAIR_COLUMNS = [
    "signal_date",
    "signal_available_date",
    "model_id",
    "model_name",
    "global_cb_index",
    "global_cb_momentum_score",
    "global_cb_regime",
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

GLOBAL_MARKET_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "availability_lag_months",
    "horizon_months",
    "sample_policy",
    "observations",
    "correlation",
    "mean_return",
    "median_return",
    "positive_share",
    "classification",
]


def build_global_bitcoin_pairs(
    global_index: pd.DataFrame,
    market_levels: pd.DataFrame,
    *,
    availability_lag_months: Sequence[int],
    forward_horizons_months: Sequence[int],
    max_market_staleness_days: int = 3,
) -> pd.DataFrame:
    """Pair current-vintage monthly Model G readings with later Bitcoin returns.

    Availability delays are explicit sensitivity assumptions, not reconstructed BIS publication
    dates. The latest Bitcoin observation on or before each target date is used within a strict
    staleness limit. Market outcomes never enter the global index calculation.
    """
    signal_required = {
        "date",
        "global_cb_index",
        "global_cb_momentum_score",
        "global_cb_regime",
        "global_cb_index_name",
    }
    market_required = {"date", "component", "series_id", "provider", "value"}
    missing_signal = sorted(signal_required - set(global_index.columns))
    missing_market = sorted(market_required - set(market_levels.columns))
    if missing_signal:
        raise GlobalMarketAnalysisError("Global index is missing: " + ", ".join(missing_signal))
    if missing_market:
        raise GlobalMarketAnalysisError("Market levels are missing: " + ", ".join(missing_market))
    lags = tuple(int(value) for value in availability_lag_months)
    horizons = tuple(int(value) for value in forward_horizons_months)
    if not lags or min(lags) < 0 or not horizons or min(horizons) < 1:
        raise GlobalMarketAnalysisError("Global market lags and horizons are invalid")
    if max_market_staleness_days < 0:
        raise GlobalMarketAnalysisError("Market staleness cannot be negative")

    signals = global_index.dropna(subset=["global_cb_momentum_score"]).copy()
    signals["date"] = pd.to_datetime(signals["date"]).dt.normalize().astype("datetime64[ns]")
    bitcoin = market_levels.loc[market_levels["component"] == "bitcoin"].copy()
    bitcoin["date"] = pd.to_datetime(bitcoin["date"]).dt.normalize().astype("datetime64[ns]")
    bitcoin["value"] = pd.to_numeric(bitcoin["value"], errors="coerce")
    bitcoin = bitcoin.dropna(subset=["date", "value"]).sort_values("date")
    if signals.empty or bitcoin.empty or (bitcoin["value"] <= 0).any():
        raise GlobalMarketAnalysisError("Global index and positive Bitcoin levels are required")
    if bitcoin.duplicated("date").any():
        raise GlobalMarketAnalysisError("Bitcoin levels contain duplicate dates")
    market_metadata = bitcoin.iloc[-1]

    frames: list[pd.DataFrame] = []
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
            candidates = _attach_prior_bitcoin_level(
                candidates,
                bitcoin,
                target_column="signal_available_date",
                observation_column="start_observation_date",
                value_column="start_value",
            )
            candidates = _attach_prior_bitcoin_level(
                candidates,
                bitcoin,
                target_column="end_target_date",
                observation_column="end_observation_date",
                value_column="end_value",
            )
            maximum_age = pd.Timedelta(days=max_market_staleness_days)
            valid = (
                (candidates["signal_available_date"] - candidates["start_observation_date"]).le(
                    maximum_age
                )
                & (candidates["end_target_date"] - candidates["end_observation_date"]).le(
                    maximum_age
                )
                & candidates["start_value"].gt(0)
                & candidates["end_value"].gt(0)
            )
            candidates = candidates.loc[valid].copy()
            candidates["model_id"] = "global_model_g"
            candidates["model_name"] = candidates["global_cb_index_name"]
            candidates["market_id"] = "bitcoin"
            candidates["series_id"] = market_metadata["series_id"]
            candidates["provider"] = market_metadata["provider"]
            candidates["availability_lag_months"] = lag
            candidates["horizon_months"] = horizon
            candidates["market_return"] = candidates["end_value"] / candidates["start_value"] - 1
            candidates["is_non_overlapping"] = False
            candidates.loc[candidates.index[::horizon], "is_non_overlapping"] = True
            candidates["timing_classification"] = "model_assumption"
            candidates["classification"] = "statistical_transformation"
            frames.append(candidates)
    if not frames:
        raise GlobalMarketAnalysisError("No Global Model G and Bitcoin pairs could be aligned")
    return (
        pd.concat(frames, ignore_index=True)[GLOBAL_MARKET_PAIR_COLUMNS]
        .sort_values(["availability_lag_months", "horizon_months", "signal_date"])
        .reset_index(drop=True)
    )


def summarize_global_bitcoin_pairs(
    pairs: pd.DataFrame,
    *,
    overlapping_min_periods: int,
    non_overlapping_min_periods: int,
) -> pd.DataFrame:
    """Summarize descriptive Model G momentum correlations with Bitcoin returns."""
    missing = sorted(set(GLOBAL_MARKET_PAIR_COLUMNS) - set(pairs.columns))
    if missing:
        raise GlobalMarketAnalysisError("Global Bitcoin pairs are missing: " + ", ".join(missing))
    if overlapping_min_periods < 3 or non_overlapping_min_periods < 3:
        raise GlobalMarketAnalysisError("Global Bitcoin summary minimums must be at least three")
    group_columns = [
        "model_id",
        "model_name",
        "market_id",
        "availability_lag_months",
        "horizon_months",
    ]
    rows: list[dict[str, object]] = []
    for policy in ("overlapping", "non_overlapping"):
        sample = pairs if policy == "overlapping" else pairs.loc[pairs["is_non_overlapping"]]
        minimum = (
            overlapping_min_periods if policy == "overlapping" else non_overlapping_min_periods
        )
        for keys, group in sample.groupby(group_columns, sort=True):
            valid = group.dropna(subset=["global_cb_momentum_score", "market_return"])
            observations = len(valid)
            correlation = (
                valid["global_cb_momentum_score"].corr(valid["market_return"])
                if observations >= minimum
                else math.nan
            )
            rows.append(
                {
                    **dict(zip(group_columns, keys, strict=True)),
                    "sample_policy": policy,
                    "observations": observations,
                    "correlation": correlation,
                    "mean_return": valid["market_return"].mean(),
                    "median_return": valid["market_return"].median(),
                    "positive_share": valid["market_return"].gt(0).mean(),
                    "classification": "descriptive_statistic",
                }
            )
    return pd.DataFrame(rows, columns=GLOBAL_MARKET_SUMMARY_COLUMNS).sort_values(
        ["sample_policy", "availability_lag_months", "horizon_months"], ignore_index=True
    )


def _attach_prior_bitcoin_level(
    candidates: pd.DataFrame,
    bitcoin: pd.DataFrame,
    *,
    target_column: str,
    observation_column: str,
    value_column: str,
) -> pd.DataFrame:
    return pd.merge_asof(
        candidates.sort_values(target_column),
        bitcoin[["date", "value"]].rename(
            columns={"date": observation_column, "value": value_column}
        ),
        left_on=target_column,
        right_on=observation_column,
        direction="backward",
    )
