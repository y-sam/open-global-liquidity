"""Predeclared robustness variants for the collateral-conditions score."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli


class CollateralRobustnessError(ValueError):
    """Raised when robustness assumptions or inputs are invalid."""


@dataclass(frozen=True, slots=True)
class RobustnessVariant:
    model_id: str
    weights: tuple[float, float, float]
    volatility: str
    normalization: str


@dataclass(frozen=True, slots=True)
class RobustnessConfig:
    rolling_window_months: int
    rolling_min_periods: int
    variants: tuple[RobustnessVariant, ...]


def load_robustness_config(path: Path) -> RobustnessConfig:
    """Load the explicitly declared, non-calibrated robustness grid."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["robustness"]
    variants = tuple(
        RobustnessVariant(
            model_id=name,
            weights=tuple(float(value) for value in values["weights"]),
            volatility=str(values["volatility"]),
            normalization=str(values["normalization"]),
        )
        for name, values in raw["variants"].items()
    )
    if (
        raw.get("classification") != "model_assumption"
        or {item.model_id for item in variants}
        != {
            "baseline",
            "equal_weight",
            "curve_volatility",
            "without_supply",
            "without_funding",
            "without_volatility",
            "rolling_36m",
        }
        or any(abs(sum(abs(weight) for weight in item.weights) - 1) > 1e-5 for item in variants)
        or any(item.volatility not in {"ten_year", "curve"} for item in variants)
        or any(item.normalization not in {"expanding", "rolling"} for item in variants)
    ):
        raise CollateralRobustnessError("Collateral robustness configuration is invalid")
    return RobustnessConfig(
        rolling_window_months=int(raw["rolling_window_months"]),
        rolling_min_periods=int(raw["rolling_min_periods"]),
        variants=variants,
    )


def calculate_robustness_signals(
    conditions: pd.DataFrame, config: RobustnessConfig
) -> pd.DataFrame:
    """Calculate declared alternatives without using asset outcomes."""
    required = {
        "date",
        "collateral_supply_growth_yoy",
        "funding_spread_bps",
        "treasury_volatility_bps",
        "treasury_volatility_curve_bps",
        "z_collateral_supply_growth_yoy",
        "z_funding_spread_bps",
        "z_treasury_volatility_bps",
        "z_treasury_volatility_curve_bps",
    }
    if required - set(conditions.columns):
        raise CollateralRobustnessError("Collateral conditions lack robustness inputs")
    frame = conditions.sort_values("date").copy()
    raw_columns = ["collateral_supply_growth_yoy", "funding_spread_bps", "treasury_volatility_bps"]
    for column in raw_columns:
        mean = (
            frame[column]
            .rolling(config.rolling_window_months, min_periods=config.rolling_min_periods)
            .mean()
        )
        std = (
            frame[column]
            .rolling(config.rolling_window_months, min_periods=config.rolling_min_periods)
            .std(ddof=0)
        )
        frame[f"rolling_z_{column}"] = (frame[column] - mean) / std.where(std > 0)
    outputs = []
    for variant in config.variants:
        if variant.normalization == "rolling":
            columns = [f"rolling_z_{column}" for column in raw_columns]
        else:
            volatility = (
                "z_treasury_volatility_curve_bps"
                if variant.volatility == "curve"
                else "z_treasury_volatility_bps"
            )
            columns = ["z_collateral_supply_growth_yoy", "z_funding_spread_bps", volatility]
        result = frame[["date"]].copy()
        result["model_id"] = variant.model_id
        result["model_name"] = variant.model_id.replace("_", " ").title()
        result["robustness_score"] = sum(
            frame[column] * weight for column, weight in zip(columns, variant.weights, strict=True)
        )
        result["robustness_index"] = momentum_to_ogli(result["robustness_score"])
        result["normalization"] = variant.normalization
        result["volatility_input"] = variant.volatility
        result["classification"] = "model_assumption"
        outputs.append(result)
    return pd.concat(outputs, ignore_index=True).sort_values(["model_id", "date"])
