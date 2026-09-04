"""Predeclared auxiliary-liquidity signals versus subsequent Bitcoin outcomes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from open_global_liquidity.analysis.bootstrap import moving_block_bootstrap_correlation


class AuxiliaryMarketAnalysisError(ValueError):
    """Raised when auxiliary-signal validation inputs or assumptions are invalid."""


@dataclass(frozen=True, slots=True)
class AuxiliarySignalDefinition:
    model_id: str
    name: str
    score_column: str
    index_column: str
    regime_column: str


@dataclass(frozen=True, slots=True)
class AuxiliaryValidationConfig:
    additional_lags_months: tuple[int, ...]
    horizons_months: tuple[int, ...]
    primary_lag_months: int
    primary_horizon_months: int
    primary_sample_policy: str
    overlapping_min_periods: int
    non_overlapping_min_periods: int
    confidence_level: float
    bootstrap_resamples: int
    bootstrap_block_length: int
    bootstrap_seed: int
    signals: tuple[AuxiliarySignalDefinition, ...]


PAIR_COLUMNS = [
    "signal_date",
    "source_available_date",
    "signal_available_date",
    "model_id",
    "model_name",
    "signal_score",
    "signal_index",
    "signal_regime",
    "market_id",
    "series_id",
    "provider",
    "additional_availability_lag_months",
    "horizon_months",
    "start_observation_date",
    "start_value",
    "end_target_date",
    "end_observation_date",
    "end_value",
    "market_return",
    "is_non_overlapping",
    "specification_role",
    "timing_classification",
    "classification",
]

SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "additional_availability_lag_months",
    "horizon_months",
    "sample_policy",
    "specification_role",
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
    "interval_reading",
    "classification",
]


def load_auxiliary_validation_config(path: Path) -> AuxiliaryValidationConfig:
    """Load the frozen, non-calibrated auxiliary-signal validation protocol."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        primary = raw["primary"]
        minimums = raw["minimum_observations"]
        bootstrap = raw["bootstrap"]
        signal_items = raw["signals"]
        signals = tuple(
            AuxiliarySignalDefinition(
                model_id=str(model_id),
                name=str(item["name"]),
                score_column=str(item["score_column"]),
                index_column=str(item["index_column"]),
                regime_column=str(item["regime_column"]),
            )
            for model_id, item in signal_items.items()
        )
        lags = tuple(int(value) for value in raw["additional_availability_lag_months"])
        horizons = tuple(int(value) for value in raw["forward_horizons_months"])
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise AuxiliaryMarketAnalysisError(
            f"Could not load auxiliary validation config: {exc}"
        ) from exc
    if (
        raw.get("classification") != "model_assumption"
        or raw.get("status") != "frozen_before_result_inspection"
        or raw.get("calibrated_parameters") != {}
        or not lags
        or min(lags) < 0
        or any(left >= right for left, right in pairwise(lags))
        or not horizons
        or min(horizons) < 1
        or any(left >= right for left, right in pairwise(horizons))
        or int(primary["additional_availability_lag_months"]) not in lags
        or int(primary["forward_horizon_months"]) not in horizons
        or primary["sample_policy"] not in {"overlapping", "non_overlapping"}
        or int(minimums["overlapping"]) < 3
        or int(minimums["non_overlapping"]) < 3
        or not 0 < float(raw["confidence_level"]) < 1
        or bootstrap.get("method") != "circular_moving_block_percentile"
        or int(bootstrap["resamples"]) < 100
        or int(bootstrap["block_length_observations"]) < 1
        or not signals
        or len({signal.model_id for signal in signals}) != len(signals)
    ):
        raise AuxiliaryMarketAnalysisError("Auxiliary validation configuration is invalid")
    return AuxiliaryValidationConfig(
        additional_lags_months=lags,
        horizons_months=horizons,
        primary_lag_months=int(primary["additional_availability_lag_months"]),
        primary_horizon_months=int(primary["forward_horizon_months"]),
        primary_sample_policy=str(primary["sample_policy"]),
        overlapping_min_periods=int(minimums["overlapping"]),
        non_overlapping_min_periods=int(minimums["non_overlapping"]),
        confidence_level=float(raw["confidence_level"]),
        bootstrap_resamples=int(bootstrap["resamples"]),
        bootstrap_block_length=int(bootstrap["block_length_observations"]),
        bootstrap_seed=int(bootstrap["seed"]),
        signals=signals,
    )


def build_auxiliary_bitcoin_pairs(
    signal_frame: pd.DataFrame,
    market_levels: pd.DataFrame,
    definition: AuxiliarySignalDefinition,
    config: AuxiliaryValidationConfig,
    *,
    max_market_staleness_days: int = 3,
) -> pd.DataFrame:
    """Pair a frozen quarterly signal with Bitcoin returns after modeled availability."""
    required = {
        "date",
        "signal_available_date",
        definition.score_column,
        definition.index_column,
        definition.regime_column,
    }
    market_required = {"date", "component", "series_id", "provider", "value"}
    if required - set(signal_frame.columns) or market_required - set(market_levels.columns):
        raise AuxiliaryMarketAnalysisError("Auxiliary signal or Bitcoin inputs are missing columns")
    signals = signal_frame.dropna(subset=[definition.score_column]).copy()
    signals["date"] = pd.to_datetime(signals["date"], errors="coerce").dt.normalize()
    signals["signal_available_date"] = pd.to_datetime(
        signals["signal_available_date"], errors="coerce"
    ).dt.normalize()
    bitcoin = market_levels.loc[market_levels["component"] == "bitcoin"].copy()
    bitcoin["date"] = (
        pd.to_datetime(bitcoin["date"], errors="coerce").dt.normalize().astype("datetime64[ns]")
    )
    bitcoin["value"] = pd.to_numeric(bitcoin["value"], errors="coerce")
    bitcoin = bitcoin.dropna(subset=["date", "value"]).sort_values("date")
    if (
        signals.empty
        or signals[["date", "signal_available_date"]].isna().any().any()
        or bitcoin.empty
        or bitcoin["date"].duplicated().any()
        or (bitcoin["value"] <= 0).any()
        or max_market_staleness_days < 0
    ):
        raise AuxiliaryMarketAnalysisError("Auxiliary signal or Bitcoin observations are invalid")
    metadata = bitcoin.iloc[-1]
    frames: list[pd.DataFrame] = []
    for lag in config.additional_lags_months:
        for horizon in config.horizons_months:
            candidates = signals.copy()
            candidates["signal_date"] = candidates["date"]
            candidates["source_available_date"] = candidates["signal_available_date"]
            candidates["signal_available_date"] = candidates[
                "source_available_date"
            ] + pd.DateOffset(months=lag)
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
                (candidates["signal_available_date"] - candidates["start_observation_date"]).le(
                    tolerance
                )
                & (candidates["end_target_date"] - candidates["end_observation_date"]).le(tolerance)
                & candidates["start_value"].gt(0)
                & candidates["end_value"].gt(0)
            )
            candidates = candidates.loc[valid].sort_values("signal_available_date").copy()
            candidates["model_id"] = definition.model_id
            candidates["model_name"] = definition.name
            candidates["signal_score"] = candidates[definition.score_column]
            candidates["signal_index"] = candidates[definition.index_column]
            candidates["signal_regime"] = candidates[definition.regime_column]
            candidates["market_id"] = "bitcoin"
            candidates["series_id"] = metadata["series_id"]
            candidates["provider"] = metadata["provider"]
            candidates["additional_availability_lag_months"] = lag
            candidates["horizon_months"] = horizon
            candidates["market_return"] = candidates["end_value"] / candidates["start_value"] - 1
            candidates["is_non_overlapping"] = _non_overlapping_mask(candidates)
            primary = lag == config.primary_lag_months and horizon == config.primary_horizon_months
            candidates["specification_role"] = "primary" if primary else "robustness"
            candidates["timing_classification"] = "source_timed_plus_model_assumption"
            candidates["classification"] = "statistical_transformation"
            frames.append(candidates[PAIR_COLUMNS])
    if not frames:
        raise AuxiliaryMarketAnalysisError("No auxiliary-signal Bitcoin pairs could be aligned")
    return pd.concat(frames, ignore_index=True).sort_values(
        ["model_id", "additional_availability_lag_months", "horizon_months", "signal_date"],
        ignore_index=True,
    )


def summarize_auxiliary_bitcoin_pairs(
    pairs: pd.DataFrame, config: AuxiliaryValidationConfig
) -> pd.DataFrame:
    """Summarize predeclared auxiliary-signal tests with two uncertainty estimators."""
    if set(PAIR_COLUMNS) - set(pairs.columns):
        raise AuxiliaryMarketAnalysisError("Auxiliary Bitcoin pairs are missing columns")
    rows: list[dict[str, object]] = []
    groups = [
        "model_id",
        "model_name",
        "market_id",
        "additional_availability_lag_months",
        "horizon_months",
        "specification_role",
    ]
    group_number = 0
    for policy in ("overlapping", "non_overlapping"):
        sample = pairs if policy == "overlapping" else pairs.loc[pairs["is_non_overlapping"]]
        minimum = (
            config.overlapping_min_periods
            if policy == "overlapping"
            else config.non_overlapping_min_periods
        )
        for keys, group in sample.groupby(groups, sort=True):
            valid = group.dropna(subset=["signal_score", "market_return"])
            observations = len(valid)
            correlation = (
                valid["signal_score"].corr(valid["market_return"])
                if observations >= minimum
                else math.nan
            )
            fisher_lower = fisher_upper = bootstrap_lower = bootstrap_upper = math.nan
            bootstrap_valid = 0
            if pd.notna(correlation):
                if observations > 3 and abs(correlation) < 1:
                    transformed = np.arctanh(correlation)
                    critical = stats.norm.ppf((1 + config.confidence_level) / 2)
                    fisher_lower, fisher_upper = np.tanh(
                        [
                            transformed - critical / np.sqrt(observations - 3),
                            transformed + critical / np.sqrt(observations - 3),
                        ]
                    )
                else:
                    fisher_lower = fisher_upper = correlation
                bootstrap_lower, bootstrap_upper, bootstrap_valid = (
                    moving_block_bootstrap_correlation(
                        valid["signal_score"],
                        valid["market_return"],
                        confidence_level=config.confidence_level,
                        resamples=config.bootstrap_resamples,
                        block_length=config.bootstrap_block_length,
                        seed=config.bootstrap_seed + group_number,
                    )
                )
            if pd.isna(correlation):
                interval_reading = "Insufficient sample"
            elif bootstrap_lower <= 0 <= bootstrap_upper:
                interval_reading = "Inconclusive"
            elif bootstrap_lower > 0:
                interval_reading = "Positive association"
            else:
                interval_reading = "Negative association"
            rows.append(
                {
                    **dict(zip(groups, keys, strict=True)),
                    "sample_policy": policy,
                    "specification_role": (
                        "primary"
                        if keys[-1] == "primary" and policy == config.primary_sample_policy
                        else "robustness"
                    ),
                    "observations": observations,
                    "correlation": correlation,
                    "correlation_ci_lower": fisher_lower,
                    "correlation_ci_upper": fisher_upper,
                    "bootstrap_ci_lower": bootstrap_lower,
                    "bootstrap_ci_upper": bootstrap_upper,
                    "bootstrap_valid_resamples": bootstrap_valid,
                    "bootstrap_block_length": config.bootstrap_block_length,
                    "bootstrap_seed": config.bootstrap_seed + group_number,
                    "mean_return": valid["market_return"].mean(),
                    "median_return": valid["market_return"].median(),
                    "positive_share": valid["market_return"].gt(0).mean(),
                    "interval_reading": interval_reading,
                    "classification": "descriptive_statistic",
                }
            )
            group_number += 1
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS).sort_values(
        ["model_id", "sample_policy", "additional_availability_lag_months", "horizon_months"],
        ignore_index=True,
    )


def _non_overlapping_mask(frame: pd.DataFrame) -> pd.Series:
    """Greedily retain chronologically adjacent return windows that do not overlap."""
    selected = pd.Series(False, index=frame.index)
    last_end: pd.Timestamp | None = None
    for index, row in frame.sort_values("signal_available_date").iterrows():
        start = pd.Timestamp(row["signal_available_date"])
        if last_end is None or start >= last_end:
            selected.loc[index] = True
            last_end = pd.Timestamp(row["end_target_date"])
    return selected
