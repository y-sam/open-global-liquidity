"""Transparent currency normalization and central-bank asset aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml


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
class GlobalAggregationConfig:
    """Auditable assumptions for the v0.3 balanced quarterly aggregate."""

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
    }
    if not isinstance(raw, dict) or required - raw.keys():
        missing = sorted(required - raw.keys()) if isinstance(raw, dict) else sorted(required)
        raise GlobalAggregationError("Global aggregation config is missing: " + ", ".join(missing))
    if raw["classification"] != "model_assumption":
        raise GlobalAggregationError("Global aggregation must be a model_assumption")
    if raw["base_currency"] != "USD" or raw["canonical_frequency"] != "quarter_end":
        raise GlobalAggregationError("v0.3 requires USD and quarter_end")
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
    return GlobalAggregationConfig(
        classification="model_assumption",
        name=str(raw["name"]),
        description=str(raw["description"]),
        base_currency="USD",
        canonical_frequency="quarter_end",
        start=start,
        alignment_policy=str(raw["alignment_policy"]),
        missing_policy="balanced_panel_only",
        components=tuple(components),
        fx_max_staleness_days=fx_staleness,
    )


def calculate_global_central_bank_assets(
    source: pd.DataFrame,
    fx: pd.DataFrame,
    config: GlobalAggregationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert configured native stocks at quarter-end spot rates and form a balanced sum.

    For direct quotes (USD per native currency), native-currency millions are multiplied by the
    FX rate. For inverse quotes (native currency per USD), they are divided by the rate. The
    function uses backward as-of matching within explicit staleness limits and never interpolates.
    Only quarters with every configured component are retained in the aggregate.
    """
    required = {"date", "component", "value", "unit"}
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
    quarter_ends = pd.date_range(pd.Timestamp(config.start), latest_common, freq="QE")
    if quarter_ends.empty:
        raise GlobalAggregationError("No quarter ends fall inside the balanced source range")

    rows: list[pd.DataFrame] = []
    targets = pd.DataFrame({"date": quarter_ends})
    for item in config.components:
        observations = (
            source.loc[source["component"] == item.component, ["date", "value", "unit"]]
            .dropna(subset=["value"])
            .sort_values("date")
        )
        units = set(observations["unit"].dropna())
        if units != {item.native_unit}:
            raise GlobalAggregationError(
                f"{item.component} units {sorted(units)} do not match {item.native_unit}"
            )
        observations = observations.rename(columns={"date": "source_date", "value": "native_value"})
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
            aligned["value_usd_millions"] = aligned["native_millions"]
        else:
            fx_observations = (
                fx.loc[fx["component"] == item.fx_component, ["date", "value"]]
                .dropna(subset=["value"])
                .sort_values("date")
            )
            if fx_observations.empty:
                raise GlobalAggregationError(f"FX source is missing {item.fx_component}")
            fx_observations = fx_observations.rename(
                columns={"date": "fx_date", "value": "fx_rate"}
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
        raise GlobalAggregationError("No complete balanced quarter remains after alignment")
    aggregate = (
        balanced.groupby("date", as_index=False)
        .agg(
            total_usd_millions=("value_usd_millions", "sum"),
            component_count=("component", "nunique"),
        )
        .sort_values("date")
    )
    aggregate["total_usd_trillions"] = aggregate["total_usd_millions"] / 1_000_000
    aggregate["change_1q"] = aggregate["total_usd_millions"].pct_change()
    aggregate["growth_yoy"] = aggregate["total_usd_millions"].pct_change(4)
    aggregate["classification"] = config.classification
    aggregate["name"] = config.name
    return detail.reset_index(drop=True), aggregate.reset_index(drop=True)
