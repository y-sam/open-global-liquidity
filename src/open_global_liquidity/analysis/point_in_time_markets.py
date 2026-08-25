"""Monthly point-in-time OGLI versus subsequent public market outcomes."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import pandas as pd


class PointInTimeMarketError(ValueError):
    """Raised when point-in-time market inputs cannot support the requested analysis."""


PAIR_COLUMNS = [
    "information_date",
    "signal_observation_date",
    "signal_available_date",
    "model_id",
    "model_name",
    "vintage_ogli",
    "vintage_momentum_score",
    "vintage_regime",
    "market_id",
    "series_id",
    "provider",
    "unit",
    "source_frequency",
    "publication_lag_weeks",
    "horizon_months",
    "start_target_date",
    "start_observation_date",
    "start_value",
    "end_target_date",
    "end_observation_date",
    "end_value",
    "market_return",
    "is_non_overlapping",
    "classification",
]

SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "observations",
    "correlation",
    "mean_return",
    "median_return",
    "positive_share",
    "classification",
]


def build_point_in_time_market_pairs(
    point_in_time: pd.DataFrame,
    market_levels: pd.DataFrame,
    *,
    publication_lag_weeks: Sequence[int],
    forward_horizons_months: Sequence[int],
    max_staleness_days: Mapping[str, int] | None = None,
) -> pd.DataFrame:
    """Align month-end vintage signals with later market returns without look-ahead.

    The configured publication lag delays the assumed date on which a sealed month-end OGLI
    information set can be acted upon. Start and end levels are the latest public observations on
    or before their target dates. This is a retrospective statistical transformation; no market
    outcome enters the construction of OGLI.
    """
    signal_required = {
        "information_date",
        "signal_observation_date",
        "model_id",
        "model_name",
        "vintage_ogli",
        "vintage_momentum_score",
        "vintage_regime",
    }
    market_required = {
        "date",
        "component",
        "series_id",
        "provider",
        "value",
        "unit",
        "frequency",
    }
    missing_signal = sorted(signal_required - set(point_in_time.columns))
    missing_market = sorted(market_required - set(market_levels.columns))
    if missing_signal:
        raise PointInTimeMarketError(
            "Point-in-time signals are missing: " + ", ".join(missing_signal)
        )
    if missing_market:
        raise PointInTimeMarketError("Market levels are missing: " + ", ".join(missing_market))
    if point_in_time.empty or market_levels.empty:
        raise PointInTimeMarketError("Point-in-time signals and market levels cannot be empty")
    lags = tuple(int(item) for item in publication_lag_weeks)
    horizons = tuple(int(item) for item in forward_horizons_months)
    if not lags or any(item < 0 for item in lags):
        raise PointInTimeMarketError("Publication lags must be non-negative")
    if not horizons or any(item < 1 for item in horizons):
        raise PointInTimeMarketError("Forward horizons must be positive")

    signals = point_in_time[list(signal_required)].copy()
    signals["information_date"] = pd.to_datetime(signals["information_date"]).dt.normalize()
    signals["signal_observation_date"] = pd.to_datetime(
        signals["signal_observation_date"]
    ).dt.normalize()
    levels = market_levels.copy()
    levels["date"] = pd.to_datetime(levels["date"]).dt.normalize()
    levels["value"] = pd.to_numeric(levels["value"], errors="coerce")
    levels = levels.dropna(subset=["date", "value"])
    if levels.duplicated(["component", "date"]).any():
        raise PointInTimeMarketError("Market levels contain duplicate component/date observations")

    staleness = {"bitcoin": 3, "broad_usd_index": 10, "gold": 40}
    if max_staleness_days is not None:
        staleness.update(max_staleness_days)
    result_frames: list[pd.DataFrame] = []
    for market_id, market in levels.groupby("component", sort=True):
        market = market.sort_values("date")
        metadata = market.iloc[-1]
        for lag in lags:
            starts = signals.copy()
            starts["signal_available_date"] = starts["information_date"] + pd.Timedelta(weeks=lag)
            for horizon in horizons:
                candidates = starts.copy()
                candidates["publication_lag_weeks"] = lag
                candidates["horizon_months"] = horizon
                candidates["start_target_date"] = candidates["signal_available_date"]
                candidates["end_target_date"] = candidates["signal_available_date"] + pd.DateOffset(
                    months=horizon
                )
                candidates = _attach_prior_level(
                    candidates,
                    market,
                    target_column="start_target_date",
                    observation_column="start_observation_date",
                    value_column="start_value",
                )
                candidates = _attach_prior_level(
                    candidates,
                    market,
                    target_column="end_target_date",
                    observation_column="end_observation_date",
                    value_column="end_value",
                )
                maximum_age = staleness.get(str(market_id), 10)
                start_age = candidates["start_target_date"] - candidates["start_observation_date"]
                end_age = candidates["end_target_date"] - candidates["end_observation_date"]
                valid = (
                    candidates["start_value"].gt(0)
                    & candidates["end_value"].gt(0)
                    & start_age.le(pd.Timedelta(days=maximum_age))
                    & end_age.le(pd.Timedelta(days=maximum_age))
                )
                candidates = candidates.loc[valid].copy()
                candidates["market_return"] = (
                    candidates["end_value"] / candidates["start_value"] - 1.0
                )
                candidates["market_id"] = market_id
                candidates["series_id"] = metadata["series_id"]
                candidates["provider"] = metadata["provider"]
                candidates["unit"] = metadata["unit"]
                candidates["source_frequency"] = metadata["frequency"]
                candidates["classification"] = "statistical_transformation"
                result_frames.append(candidates)
    if not result_frames:
        raise PointInTimeMarketError("No point-in-time market pairs could be aligned")
    result = pd.concat(result_frames, ignore_index=True)
    result["is_non_overlapping"] = False
    group_columns = ["model_id", "market_id", "publication_lag_weeks", "horizon_months"]
    for _, index in result.sort_values("information_date").groupby(group_columns).groups.items():
        ordered = list(index)
        horizon = int(result.loc[ordered[0], "horizon_months"])
        result.loc[ordered[::horizon], "is_non_overlapping"] = True
    return (
        result[PAIR_COLUMNS]
        .sort_values(
            ["market_id", "model_id", "publication_lag_weeks", "horizon_months", "information_date"]
        )
        .reset_index(drop=True)
    )


def summarize_point_in_time_market_pairs(
    pairs: pd.DataFrame,
    *,
    min_periods: int = 12,
) -> pd.DataFrame:
    """Calculate descriptive correlations and return statistics for both sample policies."""
    missing = sorted(set(PAIR_COLUMNS) - set(pairs.columns))
    if missing:
        raise PointInTimeMarketError(
            "Point-in-time market pairs are missing: " + ", ".join(missing)
        )
    if min_periods < 3:
        raise PointInTimeMarketError("min_periods must be at least 3")
    groups = [
        "model_id",
        "model_name",
        "market_id",
        "series_id",
        "publication_lag_weeks",
        "horizon_months",
    ]
    rows: list[dict[str, object]] = []
    for sample_policy in ("overlapping", "non_overlapping"):
        sample = pairs if sample_policy == "overlapping" else pairs.loc[pairs["is_non_overlapping"]]
        for keys, group in sample.groupby(groups, sort=True):
            valid = group.dropna(subset=["vintage_momentum_score", "market_return"])
            observations = len(valid)
            correlation = (
                valid["vintage_momentum_score"].corr(valid["market_return"])
                if observations >= min_periods
                else math.nan
            )
            rows.append(
                {
                    **dict(zip(groups, keys, strict=True)),
                    "sample_policy": sample_policy,
                    "observations": observations,
                    "correlation": correlation,
                    "mean_return": valid["market_return"].mean(),
                    "median_return": valid["market_return"].median(),
                    "positive_share": valid["market_return"].gt(0).mean(),
                    "classification": "descriptive_statistic",
                }
            )
    return (
        pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
        .sort_values(
            ["market_id", "model_id", "sample_policy", "publication_lag_weeks", "horizon_months"]
        )
        .reset_index(drop=True)
    )


def _attach_prior_level(
    candidates: pd.DataFrame,
    market: pd.DataFrame,
    *,
    target_column: str,
    observation_column: str,
    value_column: str,
) -> pd.DataFrame:
    left = candidates.sort_values(target_column)
    right = market[["date", "value"]].rename(
        columns={"date": observation_column, "value": value_column}
    )
    return pd.merge_asof(
        left,
        right.sort_values(observation_column),
        left_on=target_column,
        right_on=observation_column,
        direction="backward",
        allow_exact_matches=True,
    )
