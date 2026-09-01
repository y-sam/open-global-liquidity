"""Transparent currency normalization and central-bank asset aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from pathlib import Path

import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli
from open_global_liquidity.transforms.normalize import historical_zscore


class GlobalAggregationError(ValueError):
    """Raised when the configured balanced global aggregate cannot be constructed safely."""


@dataclass(frozen=True, slots=True)
class GlobalComponentConfig:
    """Currency translation policy for one central-bank balance-sheet series."""

    component: str
    central_bank: str
    native_unit: str
    native_millions_multiplier: float
    max_staleness_days: int
    fx_component: str | None
    fx_quote: str


@dataclass(frozen=True, slots=True)
class GlobalIndexConfig:
    """Transparent statistical assumptions for the global central-bank momentum index."""

    name: str
    classification: str
    description: str
    normalization: str
    min_periods: int
    momentum_weights: dict[str, float]
    regimes: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class GlobalMarketAnalysisConfig:
    """Predeclared current-vintage Global Model G versus Bitcoin assumptions."""

    classification: str
    description: str
    availability_lag_months: tuple[int, ...]
    forward_horizons_months: tuple[int, ...]
    primary_availability_lag_months: int
    overlapping_min_periods: int
    non_overlapping_min_periods: int


@dataclass(frozen=True, slots=True)
class GlobalAggregationConfig:
    """Auditable assumptions for the v0.3 balanced period-end aggregate."""

    classification: str
    name: str
    description: str
    base_currency: str
    canonical_frequency: str
    start: date
    alignment_policy: str
    missing_policy: str
    components: tuple[GlobalComponentConfig, ...]
    fx_max_staleness_days: int
    index: GlobalIndexConfig
    market_analysis: GlobalMarketAnalysisConfig


def load_global_aggregation_config(path: Path) -> GlobalAggregationConfig:
    """Load and validate the deliberately small v0.3 aggregation configuration."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise GlobalAggregationError(f"Could not load global aggregation config: {exc}") from exc
    required = {
        "classification",
        "name",
        "description",
        "base_currency",
        "canonical_frequency",
        "start",
        "alignment_policy",
        "missing_policy",
        "components",
        "fx_max_staleness_days",
        "index",
        "market_analysis",
    }
    if not isinstance(raw, dict) or required - raw.keys():
        missing = sorted(required - raw.keys()) if isinstance(raw, dict) else sorted(required)
        raise GlobalAggregationError("Global aggregation config is missing: " + ", ".join(missing))
    if raw["classification"] != "model_assumption":
        raise GlobalAggregationError("Global aggregation must be a model_assumption")
    if raw["base_currency"] != "USD" or raw["canonical_frequency"] not in {
        "month_end",
        "quarter_end",
    }:
        raise GlobalAggregationError("Global aggregation requires USD and a supported frequency")
    if raw["missing_policy"] != "balanced_panel_only":
        raise GlobalAggregationError("v0.3 requires balanced_panel_only")
    components_raw = raw["components"]
    if not isinstance(components_raw, dict) or not components_raw:
        raise GlobalAggregationError("Global aggregation components must be a mapping")
    components: list[GlobalComponentConfig] = []
    component_fields = {
        "central_bank",
        "native_unit",
        "native_millions_multiplier",
        "max_staleness_days",
        "fx_component",
        "fx_quote",
    }
    for component, values in components_raw.items():
        if not isinstance(values, dict) or component_fields - values.keys():
            raise GlobalAggregationError(f"Global component {component} is incomplete")
        quote = str(values["fx_quote"])
        if quote not in {"usd_per_native", "native_per_usd"}:
            raise GlobalAggregationError(f"Global component {component} has unsupported FX quote")
        components.append(
            GlobalComponentConfig(
                component=str(component),
                central_bank=str(values["central_bank"]),
                native_unit=str(values["native_unit"]),
                native_millions_multiplier=float(values["native_millions_multiplier"]),
                max_staleness_days=int(values["max_staleness_days"]),
                fx_component=(
                    None if values["fx_component"] is None else str(values["fx_component"])
                ),
                fx_quote=quote,
            )
        )
    try:
        start = date.fromisoformat(str(raw["start"]))
        fx_staleness = int(raw["fx_max_staleness_days"])
    except (TypeError, ValueError) as exc:
        raise GlobalAggregationError("Global aggregation dates/staleness are invalid") from exc
    if fx_staleness < 0 or any(item.max_staleness_days < 0 for item in components):
        raise GlobalAggregationError("Global aggregation staleness cannot be negative")
    index_raw = raw["index"]
    index_required = {
        "name",
        "classification",
        "description",
        "normalization",
        "min_periods",
        "momentum_weights",
        "regimes",
    }
    if not isinstance(index_raw, dict) or index_required - index_raw.keys():
        raise GlobalAggregationError("Global index configuration is incomplete")
    weights = {str(key): float(value) for key, value in index_raw["momentum_weights"].items()}
    expected_growth = (
        "monthly_annualized_growth"
        if raw["canonical_frequency"] == "month_end"
        else "quarterly_annualized_growth"
    )
    if (
        set(weights) != {expected_growth, "growth_yoy"}
        or not abs(sum(weights.values()) - 1.0) < 1e-12
    ):
        raise GlobalAggregationError(
            "Global index weights must contain the two growth rates and sum to one"
        )
    regimes = tuple((str(item["label"]), float(item["max"])) for item in index_raw["regimes"])
    if (
        not regimes
        or regimes[-1][1] != 100
        or any(current[1] <= previous[1] for previous, current in pairwise(regimes))
    ):
        raise GlobalAggregationError("Global index regime thresholds must increase through 100")
    index_config = GlobalIndexConfig(
        name=str(index_raw["name"]),
        classification=str(index_raw["classification"]),
        description=str(index_raw["description"]),
        normalization=str(index_raw["normalization"]),
        min_periods=int(index_raw["min_periods"]),
        momentum_weights=weights,
        regimes=regimes,
    )
    if (
        index_config.classification != "statistical_transformation"
        or index_config.normalization != "expanding"
        or index_config.min_periods < 4
    ):
        raise GlobalAggregationError(
            "Global index must use expanding normalization with at least four periods"
        )
    market_raw = raw["market_analysis"]
    market_required = {
        "classification",
        "description",
        "availability_lag_months",
        "forward_horizons_months",
        "primary_availability_lag_months",
        "overlapping_min_periods",
        "non_overlapping_min_periods",
    }
    if not isinstance(market_raw, dict) or market_required - market_raw.keys():
        raise GlobalAggregationError("Global market-analysis configuration is incomplete")
    market_config = GlobalMarketAnalysisConfig(
        classification=str(market_raw["classification"]),
        description=str(market_raw["description"]),
        availability_lag_months=tuple(
            int(value) for value in market_raw["availability_lag_months"]
        ),
        forward_horizons_months=tuple(
            int(value) for value in market_raw["forward_horizons_months"]
        ),
        primary_availability_lag_months=int(market_raw["primary_availability_lag_months"]),
        overlapping_min_periods=int(market_raw["overlapping_min_periods"]),
        non_overlapping_min_periods=int(market_raw["non_overlapping_min_periods"]),
    )
    if (
        market_config.classification != "model_assumption"
        or not market_config.availability_lag_months
        or min(market_config.availability_lag_months) < 0
        or market_config.primary_availability_lag_months
        not in market_config.availability_lag_months
        or not market_config.forward_horizons_months
        or min(market_config.forward_horizons_months) < 1
        or market_config.overlapping_min_periods < 3
        or market_config.non_overlapping_min_periods < 3
    ):
        raise GlobalAggregationError("Global market-analysis assumptions are invalid")
    return GlobalAggregationConfig(
        classification="model_assumption",
        name=str(raw["name"]),
        description=str(raw["description"]),
        base_currency="USD",
        canonical_frequency=str(raw["canonical_frequency"]),
        start=start,
        alignment_policy=str(raw["alignment_policy"]),
        missing_policy="balanced_panel_only",
        components=tuple(components),
        fx_max_staleness_days=fx_staleness,
        index=index_config,
        market_analysis=market_config,
    )


def calculate_global_central_bank_index(
    aggregate: pd.DataFrame,
    config: GlobalAggregationConfig,
) -> pd.DataFrame:
    """Add a non-look-ahead 0-100 momentum index to the global asset aggregate.

    The one-period annualized growth rate and 12-month growth rate are standardized against
    expanding history only, then combined with configured weights and mapped through the standard
    normal CDF. This is deliberately named a global *central-bank* index: it does not measure bank
    credit, repo, offshore dollars, collateral, or shadow banking.
    """
    change_column = "change_1m" if config.canonical_frequency == "month_end" else "change_1q"
    required = {"date", "total_usd_millions", change_column, "growth_yoy"}
    missing = sorted(required - set(aggregate.columns))
    if missing:
        raise GlobalAggregationError("Global aggregate is missing: " + ", ".join(missing))
    result = aggregate.sort_values("date").reset_index(drop=True).copy()
    periods_per_year = 12 if config.canonical_frequency == "month_end" else 4
    annualized_column = (
        "monthly_annualized_growth"
        if config.canonical_frequency == "month_end"
        else "quarterly_annualized_growth"
    )
    result[annualized_column] = (
        result["total_usd_millions"] / result["total_usd_millions"].shift(1)
    ).pow(periods_per_year) - 1
    growth_columns = (annualized_column, "growth_yoy")
    for column in growth_columns:
        result[f"z_{column}"] = historical_zscore(
            result[column], mode="expanding", min_periods=config.index.min_periods
        )
    result["global_cb_momentum_score"] = sum(
        result[f"z_{column}"] * config.index.momentum_weights[column] for column in growth_columns
    )
    result["global_cb_index"] = momentum_to_ogli(result["global_cb_momentum_score"])
    result["global_cb_regime"] = result["global_cb_index"].map(
        lambda value: (
            None
            if pd.isna(value)
            else next(label for label, maximum in config.index.regimes if value <= maximum)
        )
    )
    result["global_cb_index_name"] = config.index.name
    result["global_cb_index_classification"] = config.index.classification
    result["global_cb_weight_classification"] = "model_assumption"
    result["global_cb_zscore_mode"] = config.index.normalization
    result["global_cb_zscore_min_periods"] = config.index.min_periods
    return result


def calculate_global_central_bank_assets(
    source: pd.DataFrame,
    fx: pd.DataFrame,
    config: GlobalAggregationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert configured native stocks at period-end spot rates and form a balanced sum.

    For direct quotes (USD per native currency), native-currency millions are multiplied by the
    FX rate. For inverse quotes (native currency per USD), they are divided by the rate. The
    function uses backward as-of matching within explicit staleness limits and never interpolates.
    Only periods with every configured component are retained in the aggregate.
    """
    required = {"date", "component", "value", "unit", "provider", "series_id", "retrieved_at"}
    for label, frame in (("central-bank source", source), ("FX source", fx)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise GlobalAggregationError(f"{label} is missing columns: {', '.join(missing)}")
    source = source.copy()
    fx = fx.copy()
    source["date"] = pd.to_datetime(source["date"])
    fx["date"] = pd.to_datetime(fx["date"])
    configured_components = {item.component for item in config.components}
    missing_components = configured_components - set(source["component"])
    if missing_components:
        raise GlobalAggregationError(
            "Central-bank source is missing configured components: "
            + ", ".join(sorted(missing_components))
        )
    latest_common = min(
        source.loc[source["component"] == item.component, "date"].max()
        for item in config.components
    )
    period_frequency = "ME" if config.canonical_frequency == "month_end" else "QE"
    period_ends = pd.date_range(pd.Timestamp(config.start), latest_common, freq=period_frequency)
    if period_ends.empty:
        raise GlobalAggregationError("No period ends fall inside the balanced source range")

    rows: list[pd.DataFrame] = []
    targets = pd.DataFrame({"date": period_ends})
    for item in config.components:
        observations = (
            source.loc[
                source["component"] == item.component,
                ["date", "value", "unit", "provider", "series_id", "retrieved_at"],
            ]
            .dropna(subset=["value"])
            .sort_values("date")
        )
        units = set(observations["unit"].dropna())
        if units != {item.native_unit}:
            raise GlobalAggregationError(
                f"{item.component} units {sorted(units)} do not match {item.native_unit}"
            )
        observations = observations.rename(
            columns={
                "date": "source_date",
                "value": "native_value",
                "provider": "source_provider",
                "series_id": "source_series_id",
                "retrieved_at": "source_retrieved_at",
            }
        )
        aligned = pd.merge_asof(
            targets,
            observations,
            left_on="date",
            right_on="source_date",
            direction="backward",
            tolerance=pd.Timedelta(days=item.max_staleness_days),
        )
        aligned["component"] = item.component
        aligned["central_bank"] = item.central_bank
        aligned["native_unit"] = item.native_unit
        aligned["native_millions"] = aligned["native_value"] * item.native_millions_multiplier
        if item.fx_component is None:
            aligned["fx_component"] = "USD"
            aligned["fx_date"] = aligned["source_date"]
            aligned["fx_rate"] = 1.0
            aligned["fx_provider"] = "Identity conversion"
            aligned["fx_series_id"] = "USD"
            aligned["fx_retrieved_at"] = aligned["source_retrieved_at"]
            aligned["value_usd_millions"] = aligned["native_millions"]
        else:
            fx_observations = (
                fx.loc[
                    fx["component"] == item.fx_component,
                    ["date", "value", "provider", "series_id", "retrieved_at"],
                ]
                .dropna(subset=["value"])
                .sort_values("date")
            )
            if fx_observations.empty:
                raise GlobalAggregationError(f"FX source is missing {item.fx_component}")
            fx_observations = fx_observations.rename(
                columns={
                    "date": "fx_date",
                    "value": "fx_rate",
                    "provider": "fx_provider",
                    "series_id": "fx_series_id",
                    "retrieved_at": "fx_retrieved_at",
                }
            )
            aligned = pd.merge_asof(
                aligned.sort_values("date"),
                fx_observations,
                left_on="date",
                right_on="fx_date",
                direction="backward",
                tolerance=pd.Timedelta(days=config.fx_max_staleness_days),
            )
            aligned["fx_component"] = item.fx_component
            if (aligned["fx_rate"] <= 0).any():
                raise GlobalAggregationError(
                    f"FX source {item.fx_component} contains nonpositive rates"
                )
            if item.fx_quote == "usd_per_native":
                aligned["value_usd_millions"] = aligned["native_millions"] * aligned["fx_rate"]
            else:
                aligned["value_usd_millions"] = aligned["native_millions"] / aligned["fx_rate"]
        rows.append(aligned)

    detail = pd.concat(rows, ignore_index=True).sort_values(["date", "component"])
    complete = detail.dropna(subset=["native_value", "fx_rate", "value_usd_millions"])
    counts = complete.groupby("date")["component"].nunique()
    balanced_dates = counts[counts == len(config.components)].index
    detail["is_balanced"] = detail["date"].isin(balanced_dates)
    balanced = detail.loc[detail["is_balanced"]].copy()
    if balanced.empty:
        raise GlobalAggregationError("No complete balanced period remains after alignment")
    aggregate = (
        balanced.groupby("date", as_index=False)
        .agg(
            total_usd_millions=("value_usd_millions", "sum"),
            component_count=("component", "nunique"),
        )
        .sort_values("date")
    )
    aggregate["total_usd_trillions"] = aggregate["total_usd_millions"] / 1_000_000
    change_column = "change_1m" if config.canonical_frequency == "month_end" else "change_1q"
    periods_per_year = 12 if config.canonical_frequency == "month_end" else 4
    aggregate[change_column] = aggregate["total_usd_millions"].pct_change()
    aggregate["growth_yoy"] = aggregate["total_usd_millions"].pct_change(periods_per_year)
    aggregate["classification"] = config.classification
    aggregate["name"] = config.name
    aggregate = calculate_global_central_bank_index(aggregate, config)
    return detail.reset_index(drop=True), aggregate.reset_index(drop=True)
