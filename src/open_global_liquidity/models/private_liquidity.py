"""US commercial-bank and money-market-fund liquidity layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli
from open_global_liquidity.transforms.normalize import historical_zscore


class PrivateLiquidityError(ValueError):
    """Raised when private-liquidity inputs or assumptions are invalid."""


@dataclass(frozen=True, slots=True)
class PrivateLiquidityConfig:
    name: str
    max_bank_staleness_days: int
    bank_weight: float
    mmf_weight: float
    qoq_weight: float
    yoy_weight: float
    min_periods: int
    availability_lag_months: int


def load_private_liquidity_config(path: Path) -> PrivateLiquidityConfig:
    """Load the declared, non-calibrated private-liquidity assumptions."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        components = raw["components"]
        momentum = raw["momentum"]
        normalization = raw["normalization"]
        availability = raw["availability"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise PrivateLiquidityError(f"Could not load private-liquidity config: {exc}") from exc
    component_weights = (
        float(components["bank_credit"]["weight"]),
        float(components["money_market_fund_assets"]["weight"]),
    )
    momentum_weights = (float(momentum["qoq_annualized_weight"]), float(momentum["yoy_weight"]))
    if (
        raw.get("classification") != "model_assumption"
        or raw.get("canonical_frequency") != "quarter_end"
        or raw.get("alignment_policy") != "latest_observation_on_or_before_quarter_end"
        or raw.get("calibrated_parameters") != {}
        or not np.isclose(sum(component_weights), 1)
        or not np.isclose(sum(momentum_weights), 1)
        or normalization.get("mode") != "expanding"
        or int(normalization.get("min_periods", 0)) < 8
        or availability.get("classification") != "model_assumption"
    ):
        raise PrivateLiquidityError("Private-liquidity configuration is invalid")
    return PrivateLiquidityConfig(
        name=str(raw["name"]),
        max_bank_staleness_days=int(raw["max_bank_staleness_days"]),
        bank_weight=component_weights[0],
        mmf_weight=component_weights[1],
        qoq_weight=momentum_weights[0],
        yoy_weight=momentum_weights[1],
        min_periods=int(normalization["min_periods"]),
        availability_lag_months=int(availability["lag_months"]),
    )


def calculate_private_liquidity(
    source: pd.DataFrame, config: PrivateLiquidityConfig
) -> pd.DataFrame:
    """Calculate a quarterly bank-credit/MMF momentum composite without double counting loans."""
    required = {"date", "component", "value", "provider", "series_id", "retrieved_at"}
    if required - set(source.columns):
        raise PrivateLiquidityError("Private-liquidity source is missing required columns")
    frame = source.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["date", "value"])
    expected = {"bank_credit", "bank_loans_and_leases", "money_market_fund_assets"}
    if expected - set(frame["component"]):
        raise PrivateLiquidityError("Private-liquidity source lacks configured components")
    mmf = frame.loc[frame["component"] == "money_market_fund_assets", ["date", "value"]].copy()
    # FRED labels Financial Accounts quarters at their first calendar day even though the source
    # metadata describes end-of-period stocks. Convert the period label explicitly; do not shift
    # or interpolate values between quarters.
    mmf["date"] = mmf["date"].dt.to_period("Q").dt.to_timestamp("Q")
    mmf = mmf.rename(columns={"value": "mmf_assets_millions"}).sort_values("date")
    quarter_ends = mmf[["date"]].copy()
    result = quarter_ends
    for component, output in (
        ("bank_credit", "bank_credit_billions"),
        ("bank_loans_and_leases", "bank_loans_billions"),
    ):
        values = frame.loc[frame["component"] == component, ["date", "value"]].sort_values("date")
        result = pd.merge_asof(
            result.sort_values("date"),
            values.rename(columns={"date": f"{output}_source_date", "value": output}),
            left_on="date",
            right_on=f"{output}_source_date",
            direction="backward",
            tolerance=pd.Timedelta(days=config.max_bank_staleness_days),
        )
    result = result.merge(mmf, on="date", how="left", validate="one_to_one")
    aligned_columns = ["bank_credit_billions", "bank_loans_billions", "mmf_assets_millions"]
    result = result.dropna(subset=aligned_columns).reset_index(drop=True)
    result = result.loc[result[aligned_columns].gt(0).all(axis=1)].reset_index(drop=True)
    if result.empty:
        raise PrivateLiquidityError("Private-liquidity alignment produced missing values")
    result["loan_share_of_bank_credit"] = (
        result["bank_loans_billions"] / result["bank_credit_billions"]
    )
    for component in ("bank_credit_billions", "mmf_assets_millions"):
        level = result[component]
        prefix = "bank" if component.startswith("bank") else "mmf"
        result[f"{prefix}_growth_qoq_annualized"] = (level / level.shift(1)).pow(4) - 1
        result[f"{prefix}_growth_yoy"] = level.pct_change(4, fill_method=None)
        for growth in ("growth_qoq_annualized", "growth_yoy"):
            result[f"z_{prefix}_{growth}"] = historical_zscore(
                result[f"{prefix}_{growth}"], mode="expanding", min_periods=config.min_periods
            )
        result[f"{prefix}_momentum"] = (
            config.qoq_weight * result[f"z_{prefix}_growth_qoq_annualized"]
            + config.yoy_weight * result[f"z_{prefix}_growth_yoy"]
        )
    result["private_liquidity_momentum"] = (
        config.bank_weight * result["bank_momentum"] + config.mmf_weight * result["mmf_momentum"]
    )
    result["private_liquidity_index"] = momentum_to_ogli(result["private_liquidity_momentum"])
    result["signal_available_date"] = result["date"] + pd.offsets.MonthEnd(
        config.availability_lag_months
    )
    result["model_name"] = config.name
    result["model_classification"] = "model_assumption"
    result["calibration_status"] = "not_calibrated"
    return result
