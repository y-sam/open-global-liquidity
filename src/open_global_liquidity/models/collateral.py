"""Transparent US Treasury collateral and secured-funding conditions pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli
from open_global_liquidity.transforms.normalize import historical_zscore


class CollateralModelError(ValueError):
    """Raised when collateral inputs or assumptions cannot produce a valid score."""


@dataclass(frozen=True, slots=True)
class CollateralComponentConfig:
    """Direction and assumed weight for one normalized collateral condition."""

    name: str
    weight: float
    direction: int
    classification: str


@dataclass(frozen=True, slots=True)
class CollateralConfig:
    """Auditable assumptions for the v0.4a collateral-conditions pilot."""

    classification: str
    name: str
    description: str
    start: date
    monthly_stock_staleness_days: int
    weekly_stock_staleness_days: int
    volatility_window: int
    volatility_min_observations: int
    volatility_annualization_factor: int
    normalization_mode: str
    normalization_min_periods: int
    components: tuple[CollateralComponentConfig, ...]
    regimes: tuple[tuple[str, float], ...]
    bitcoin_validation: CollateralBitcoinValidationConfig


@dataclass(frozen=True, slots=True)
class CollateralBitcoinValidationConfig:
    """Predeclared Bitcoin outcome-comparison settings for the frozen score."""

    signal: str
    availability_lag_months: tuple[int, ...]
    forward_horizons_months: tuple[int, ...]
    primary_availability_lag_months: int
    primary_horizon_months: int
    primary_sample_policy: str
    overlapping_min_periods: int
    non_overlapping_min_periods: int
    confidence_level: float
    bootstrap_resamples: int
    bootstrap_block_length: int
    bootstrap_seed: int


def load_collateral_config(path: Path) -> CollateralConfig:
    """Load and validate the deliberately small v0.4a configuration."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CollateralModelError(f"Could not load collateral config: {exc}") from exc
    required = {
        "classification",
        "name",
        "description",
        "canonical_frequency",
        "start",
        "alignment_policy",
        "max_staleness_days",
        "daily_aggregation",
        "private_collateral_proxy",
        "yield_volatility",
        "funding_spread",
        "normalization",
        "components",
        "regimes",
        "calibrated_parameters",
        "bitcoin_validation",
    }
    if not isinstance(raw, dict) or required - raw.keys():
        missing = sorted(required - raw.keys()) if isinstance(raw, dict) else sorted(required)
        raise CollateralModelError("Collateral config is missing: " + ", ".join(missing))
    if raw["classification"] != "model_assumption":
        raise CollateralModelError("Collateral model must be classified as model_assumption")
    if raw["canonical_frequency"] != "month_end":
        raise CollateralModelError("Collateral model requires month_end frequency")
    if raw["alignment_policy"] != "latest_observation_on_or_before_month_end":
        raise CollateralModelError("Collateral alignment policy is unsupported")
    if raw["calibrated_parameters"] != {}:
        raise CollateralModelError("v0.4a must not contain calibrated parameters")
    validation = raw["bitcoin_validation"]
    if (
        not isinstance(validation, dict)
        or validation.get("classification") != "statistical_transformation"
    ):
        raise CollateralModelError("Collateral Bitcoin validation configuration is malformed")
    bootstrap = validation.get("bootstrap", {})
    lags = tuple(int(value) for value in validation.get("availability_lag_months", []))
    horizons = tuple(int(value) for value in validation.get("forward_horizons_months", []))
    if (
        validation.get("signal") != "collateral_conditions_score"
        or not lags
        or min(lags) < 0
        or not horizons
        or min(horizons) < 1
        or validation.get("primary_sample_policy") not in {"overlapping", "non_overlapping"}
        or int(validation.get("primary_availability_lag_months", -1)) not in lags
        or int(validation.get("primary_horizon_months", -1)) not in horizons
        or int(validation.get("overlapping_min_periods", 0)) < 3
        or int(validation.get("non_overlapping_min_periods", 0)) < 3
        or not 0 < float(validation.get("confidence_level", 0)) < 1
        or bootstrap.get("method") != "circular_moving_block_percentile"
        or int(bootstrap.get("resamples", 0)) < 100
        or int(bootstrap.get("block_length_observations", 0)) < 1
    ):
        raise CollateralModelError("Collateral Bitcoin validation settings are invalid")
    if raw["daily_aggregation"] != {"funding_spread": "median", "yield_volatility": "last"}:
        raise CollateralModelError("Collateral daily aggregation policy is unsupported")

    volatility = raw["yield_volatility"]
    normalization = raw["normalization"]
    staleness = raw["max_staleness_days"]
    if not all(isinstance(item, dict) for item in (volatility, normalization, staleness)):
        raise CollateralModelError("Collateral nested configuration is malformed")
    component_raw = raw["components"]
    if not isinstance(component_raw, dict) or not component_raw:
        raise CollateralModelError("Collateral components must be a non-empty mapping")
    components = tuple(
        CollateralComponentConfig(
            name=str(name),
            weight=float(values["weight"]),
            direction=int(values["direction"]),
            classification=str(values["classification"]),
        )
        for name, values in component_raw.items()
    )
    if any(item.direction not in {-1, 1} for item in components):
        raise CollateralModelError("Collateral component directions must be -1 or 1")
    if any(item.classification != "model_assumption" for item in components):
        raise CollateralModelError("Collateral weights must be model assumptions")
    if set(item.name for item in components) != {
        "collateral_supply_growth_yoy",
        "funding_spread_bps",
        "treasury_volatility_bps",
    }:
        raise CollateralModelError("Collateral model requires the three declared components")
    if not np.isclose(sum(item.weight for item in components), 1.0):
        raise CollateralModelError("Collateral component weights must sum to one")
    regimes = tuple((str(item["label"]), float(item["max"])) for item in raw["regimes"])
    if (
        not regimes
        or regimes[-1][1] != 100
        or any(current[1] <= previous[1] for previous, current in pairwise(regimes))
    ):
        raise CollateralModelError("Collateral regimes must increase through 100")
    try:
        start = date.fromisoformat(str(raw["start"]))
        monthly_staleness = int(staleness["monthly_stock"])
        weekly_staleness = int(staleness["weekly_stock"])
        volatility_window = int(volatility["rolling_observations"])
        volatility_min = int(volatility["min_observations"])
        annualization = int(volatility["annualization_factor"])
        min_periods = int(normalization["min_periods"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CollateralModelError("Collateral numeric/date configuration is invalid") from exc
    if normalization.get("mode") != "expanding" or min_periods < 12:
        raise CollateralModelError("Collateral score requires expanding normalization")
    if min(monthly_staleness, weekly_staleness, volatility_min, annualization) <= 0:
        raise CollateralModelError("Collateral windows and staleness must be positive")
    if volatility_window < volatility_min:
        raise CollateralModelError("Volatility window cannot be shorter than its minimum")
    return CollateralConfig(
        classification=str(raw["classification"]),
        name=str(raw["name"]),
        description=str(raw["description"]),
        start=start,
        monthly_stock_staleness_days=monthly_staleness,
        weekly_stock_staleness_days=weekly_staleness,
        volatility_window=volatility_window,
        volatility_min_observations=volatility_min,
        volatility_annualization_factor=annualization,
        normalization_mode="expanding",
        normalization_min_periods=min_periods,
        components=components,
        regimes=regimes,
        bitcoin_validation=CollateralBitcoinValidationConfig(
            signal=str(validation["signal"]),
            availability_lag_months=lags,
            forward_horizons_months=horizons,
            primary_availability_lag_months=int(validation["primary_availability_lag_months"]),
            primary_horizon_months=int(validation["primary_horizon_months"]),
            primary_sample_policy=str(validation["primary_sample_policy"]),
            overlapping_min_periods=int(validation["overlapping_min_periods"]),
            non_overlapping_min_periods=int(validation["non_overlapping_min_periods"]),
            confidence_level=float(validation["confidence_level"]),
            bootstrap_resamples=int(bootstrap["resamples"]),
            bootstrap_block_length=int(bootstrap["block_length_observations"]),
            bootstrap_seed=int(bootstrap["seed"]),
        ),
    )


def calculate_collateral_conditions(
    source: pd.DataFrame,
    config: CollateralConfig,
) -> pd.DataFrame:
    """Calculate a non-look-ahead monthly collateral-conditions score.

    Gross marketable Treasury debt held by the public is reduced by Fed Treasury holdings to form
    an approximate private collateral stock. Its annual growth is supportive. A wider SOFR-minus-
    EFFR spread and higher realized 10-year yield volatility are constraining. Each component is
    standardized only against expanding history, combined with assumed weights, and mapped to
    0-100. None of these terms is an observed collateral multiplier or haircut.
    """
    required = {"date", "component", "value", "provider", "series_id", "retrieved_at"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise CollateralModelError("Collateral source is missing: " + ", ".join(missing))
    expected = {
        "marketable_treasury_debt_public",
        "fed_treasury_holdings",
        "secured_overnight_financing_rate",
        "effective_federal_funds_rate",
        "treasury_yield_10y_collateral",
    }
    absent = expected - set(source["component"])
    if absent:
        raise CollateralModelError(
            "Collateral source lacks components: " + ", ".join(sorted(absent))
        )
    frame = source.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    if frame["date"].isna().any():
        raise CollateralModelError("Collateral source contains invalid dates")
    # FRED preserves unavailable daily observations as nulls. Omit them before as-of and rolling
    # calculations rather than interpolating; declared staleness rules still govern carry-forward.
    frame = frame.dropna(subset=["value"]).copy()
    if frame.empty or expected - set(frame["component"]):
        raise CollateralModelError("Collateral source lacks usable component values")
    if frame.duplicated(["date", "component"]).any():
        raise CollateralModelError("Collateral source contains duplicate component dates")
    collateral_end = frame.loc[
        frame["component"] == "marketable_treasury_debt_public", "date"
    ].max()
    period_ends = pd.date_range(
        pd.Timestamp(config.start),
        collateral_end.to_period("M").to_timestamp("M"),
        freq="ME",
    )
    result = pd.DataFrame({"date": period_ends})
    result = _align_stock(
        result,
        frame,
        component="marketable_treasury_debt_public",
        output="gross_marketable_collateral_millions",
        tolerance_days=config.monthly_stock_staleness_days,
    )
    result = _align_stock(
        result,
        frame,
        component="fed_treasury_holdings",
        output="fed_treasury_holdings_millions",
        tolerance_days=config.weekly_stock_staleness_days,
    )
    result["private_collateral_proxy_millions"] = (
        result["gross_marketable_collateral_millions"] - result["fed_treasury_holdings_millions"]
    )
    if (result["private_collateral_proxy_millions"].dropna() <= 0).any():
        raise CollateralModelError("Private collateral proxy must remain positive")
    result["collateral_supply_growth_yoy"] = result["private_collateral_proxy_millions"].pct_change(
        12, fill_method=None
    )

    sofr = _component_series(frame, "secured_overnight_financing_rate", "sofr")
    effr = _component_series(frame, "effective_federal_funds_rate", "effr")
    funding = sofr.merge(effr, on="date", how="inner", validate="one_to_one")
    funding["funding_spread_bps"] = (funding["sofr"] - funding["effr"]) * 100
    funding["date"] = funding["date"].dt.to_period("M").dt.to_timestamp("M")
    funding_monthly = funding.groupby("date", as_index=False)["funding_spread_bps"].median()

    yields = _component_series(frame, "treasury_yield_10y_collateral", "yield_10y")
    yields["treasury_volatility_bps"] = yields["yield_10y"].diff().mul(100).rolling(
        config.volatility_window,
        min_periods=config.volatility_min_observations,
    ).std(ddof=0) * np.sqrt(config.volatility_annualization_factor)
    yields["date"] = yields["date"].dt.to_period("M").dt.to_timestamp("M")
    volatility_monthly = yields.groupby("date", as_index=False).last()[
        ["date", "treasury_volatility_bps"]
    ]
    result = result.merge(funding_monthly, on="date", how="left", validate="one_to_one")
    result = result.merge(volatility_monthly, on="date", how="left", validate="one_to_one")

    for item in config.components:
        z_column = f"z_{item.name}"
        result[z_column] = historical_zscore(
            result[item.name],
            mode="expanding",
            min_periods=config.normalization_min_periods,
        )
        result[f"contribution_{item.name}"] = result[z_column] * item.weight * item.direction
    contribution_columns = [f"contribution_{item.name}" for item in config.components]
    result["collateral_conditions_score"] = result[contribution_columns].sum(
        axis=1, min_count=len(contribution_columns)
    )
    result["collateral_conditions_index"] = momentum_to_ogli(result["collateral_conditions_score"])
    result["collateral_regime"] = result["collateral_conditions_index"].map(
        lambda value: (
            None
            if pd.isna(value)
            else next(label for label, maximum in config.regimes if value <= maximum)
        )
    )
    result["model_name"] = config.name
    result["model_classification"] = config.classification
    result["normalization_mode"] = config.normalization_mode
    result["normalization_min_periods"] = config.normalization_min_periods
    result["retrieved_at"] = frame["retrieved_at"].max()
    return result


def _component_series(frame: pd.DataFrame, component: str, output: str) -> pd.DataFrame:
    return (
        frame.loc[frame["component"] == component, ["date", "value"]]
        .dropna()
        .sort_values("date")
        .rename(columns={"value": output})
    )


def _align_stock(
    targets: pd.DataFrame,
    source: pd.DataFrame,
    *,
    component: str,
    output: str,
    tolerance_days: int,
) -> pd.DataFrame:
    observations = _component_series(source, component, output).rename(
        columns={"date": f"{output}_source_date"}
    )
    return pd.merge_asof(
        targets.sort_values("date"),
        observations,
        left_on="date",
        right_on=f"{output}_source_date",
        direction="backward",
        tolerance=pd.Timedelta(days=tolerance_days),
    )
