"""Transparent BIS offshore-dollar credit momentum layer."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli
from open_global_liquidity.transforms.normalize import historical_zscore


class CrossBorderModelError(ValueError):
    """Raised when offshore-dollar model inputs or assumptions are invalid."""


@dataclass(frozen=True, slots=True)
class CrossBorderConfig:
    """Auditable assumptions for the quarterly offshore-dollar layer."""

    name: str
    source_component: str
    availability_lag_months: int
    qoq_annualized_weight: float
    yoy_weight: float
    normalization_min_periods: int
    regimes: tuple[tuple[str, float], ...]


def load_cross_border_config(path: Path) -> CrossBorderConfig:
    """Load and validate the separate, non-calibrated cross-border model assumptions."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        availability = raw["availability"]
        momentum = raw["momentum"]
        normalization = raw["normalization"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise CrossBorderModelError(f"Could not load cross-border config: {exc}") from exc
    weights = (float(momentum["qoq_annualized_weight"]), float(momentum["yoy_weight"]))
    regimes = tuple((str(item["label"]), float(item["max"])) for item in raw["regimes"])
    if (
        raw.get("classification") != "model_assumption"
        or raw.get("canonical_frequency") != "quarter_end"
        or raw.get("calibrated_parameters") != {}
        or availability.get("classification") != "model_assumption"
        or int(availability.get("lag_months", -1)) < 0
        or momentum.get("classification") != "model_assumption"
        or not np.isclose(sum(weights), 1.0)
        or min(weights) < 0
        or normalization.get("classification") != "statistical_transformation"
        or normalization.get("mode") != "expanding"
        or int(normalization.get("min_periods", 0)) < 8
        or not regimes
        or regimes[-1][1] != 100
        or any(current[1] <= previous[1] for previous, current in pairwise(regimes))
    ):
        raise CrossBorderModelError("Cross-border configuration is invalid")
    return CrossBorderConfig(
        name=str(raw["name"]),
        source_component=str(raw["source_component"]),
        availability_lag_months=int(availability["lag_months"]),
        qoq_annualized_weight=weights[0],
        yoy_weight=weights[1],
        normalization_min_periods=int(normalization["min_periods"]),
        regimes=regimes,
    )


def calculate_cross_border_credit(source: pd.DataFrame, config: CrossBorderConfig) -> pd.DataFrame:
    """Calculate non-look-ahead momentum in measured offshore US-dollar credit.

    The measured stock includes bank loans and debt securities to non-bank borrowers outside the
    United States. Fast quarterly and annual growth are standardized against expanding history,
    combined using declared weights, and mapped through the normal CDF. This does not measure FX
    swaps, collateral reuse, credit quality, or all forms of offshore dollar funding.
    """
    required = {"date", "component", "value", "provider", "series_id", "retrieved_at"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise CrossBorderModelError("Cross-border source is missing: " + ", ".join(missing))
    frame = source.loc[source["component"] == config.source_component].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["date", "value"]).sort_values("date")
    if frame.empty or frame["date"].duplicated().any() or (frame["value"] <= 0).any():
        raise CrossBorderModelError("Cross-border source requires unique positive observations")
    result = frame[["date", "value", "provider", "series_id", "retrieved_at"]].rename(
        columns={"value": "usd_credit_nonbanks_outside_us_millions"}
    )
    credit = result["usd_credit_nonbanks_outside_us_millions"]
    result["growth_qoq_annualized"] = (credit / credit.shift(1)).pow(4) - 1
    result["growth_12m_yoy"] = credit.pct_change(4, fill_method=None)
    result["z_growth_qoq_annualized"] = historical_zscore(
        result["growth_qoq_annualized"],
        mode="expanding",
        min_periods=config.normalization_min_periods,
    )
    result["z_growth_12m_yoy"] = historical_zscore(
        result["growth_12m_yoy"],
        mode="expanding",
        min_periods=config.normalization_min_periods,
    )
    result["momentum_score"] = (
        config.qoq_annualized_weight * result["z_growth_qoq_annualized"]
        + config.yoy_weight * result["z_growth_12m_yoy"]
    )
    result["offshore_dollar_credit_index"] = momentum_to_ogli(result["momentum_score"])
    result["regime"] = result["offshore_dollar_credit_index"].map(
        lambda value: next(
            (label for label, maximum in config.regimes if pd.notna(value) and value <= maximum),
            pd.NA,
        )
    )
    result["signal_available_date"] = result["date"] + pd.offsets.MonthEnd(
        config.availability_lag_months
    )
    result["model_name"] = config.name
    result["model_classification"] = "model_assumption"
    result["normalization_classification"] = "statistical_transformation"
    result["availability_classification"] = "model_assumption"
    result["calibration_status"] = "not_calibrated"
    return result.reset_index(drop=True)
