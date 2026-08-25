"""Point-in-time OGLI calculations from explicit ALFRED information sets."""

from __future__ import annotations

from datetime import date

import pandas as pd

from open_global_liquidity.config import ModelConfig
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame
from open_global_liquidity.data.fred import VINTAGE_COLUMNS
from open_global_liquidity.models.ogli import calculate_ogli
from open_global_liquidity.models.us_liquidity import calculate_us_liquidity_models
from open_global_liquidity.transforms.frequency import align_to_weekly_wednesday
from open_global_liquidity.transforms.growth import calculate_liquidity_momentum
from open_global_liquidity.transforms.units import convert_to_usd_millions


class PointInTimeError(ValueError):
    """Raised when vintage inputs cannot support an auditable point-in-time result."""


POINT_IN_TIME_COLUMNS = [
    "information_date",
    "signal_observation_date",
    "model_id",
    "model_name",
    "vintage_ogli",
    "vintage_momentum_score",
    "vintage_regime",
    "vintage_growth_3m_annualized",
    "vintage_growth_12m_yoy",
    "zscore_mode",
    "zscore_min_periods",
    "information_set_classification",
    "retrieved_at",
]


def build_month_end_grid(start: str | date, end: str | date) -> tuple[date, ...]:
    """Return completed calendar month ends inside an inclusive date window."""
    start_timestamp = _coerce_timestamp(start, "start")
    end_timestamp = _coerce_timestamp(end, "end")
    if end_timestamp < start_timestamp:
        raise PointInTimeError("end must be on or after start")

    first = start_timestamp + pd.offsets.MonthEnd(0)
    month_end = end_timestamp + pd.offsets.MonthEnd(0)
    last = end_timestamp if end_timestamp == month_end else end_timestamp + pd.offsets.MonthEnd(-1)
    if last < first:
        return ()
    return tuple(item.date() for item in pd.date_range(first, last, freq="ME"))


def calculate_point_in_time_ogli(
    vintage_inputs: pd.DataFrame,
    config: ModelConfig,
) -> pd.DataFrame:
    """Calculate each vintage independently and retain its latest available OGLI.

    Each information date is treated as a sealed data set: units, weekly alignment, model levels,
    growth rates, and expanding normalization are recomputed using only observations ALFRED made
    available by that date. No value from a later vintage enters an earlier calculation.
    """
    missing = sorted(set(VINTAGE_COLUMNS) - set(vintage_inputs.columns))
    if missing:
        raise PointInTimeError(f"Vintage inputs are missing columns: {', '.join(missing)}")
    if vintage_inputs.empty:
        raise PointInTimeError("Vintage inputs contain no observations")
    if vintage_inputs.duplicated(["vintage_date", "component", "observation_date"]).any():
        raise PointInTimeError("Vintage inputs contain duplicate information-set observations")

    results: list[dict[str, object]] = []
    for information_date, information_set in vintage_inputs.groupby("vintage_date", sort=True):
        standardized = information_set.rename(columns={"observation_date": "date"})[
            STANDARD_COLUMNS
        ].copy()
        validate_standardized_frame(standardized)
        weekly = align_to_weekly_wednesday(
            convert_to_usd_millions(standardized),
            daily_asof_components=config.alignment.daily_asof_components,
            daily_asof_max_staleness_days=config.alignment.daily_asof_max_staleness_days,
        )
        models = calculate_us_liquidity_models(weekly, config.models)
        ogli = calculate_ogli(calculate_liquidity_momentum(models), config.ogli)
        available = ogli.dropna(subset=["ogli"])
        if available.empty:
            raise PointInTimeError(
                f"Information set {pd.Timestamp(information_date).date()} has no available OGLI; "
                "extend the source-history start or reduce the configured normalization history"
            )
        latest = (
            available.sort_values(["model_id", "date"]).groupby("model_id", as_index=False).tail(1)
        )
        if set(latest["model_id"]) != {definition.model_id for definition in config.models}:
            raise PointInTimeError(
                f"Information set {pd.Timestamp(information_date).date()} does not support all "
                "configured liquidity models"
            )
        retrieved_at = information_set["retrieved_at"].max()
        for row in latest.itertuples(index=False):
            results.append(
                {
                    "information_date": pd.Timestamp(information_date),
                    "signal_observation_date": row.date,
                    "model_id": row.model_id,
                    "model_name": row.model_name,
                    "vintage_ogli": row.ogli,
                    "vintage_momentum_score": row.momentum_score,
                    "vintage_regime": row.regime,
                    "vintage_growth_3m_annualized": row.growth_3m_annualized,
                    "vintage_growth_12m_yoy": row.growth_12m_yoy,
                    "zscore_mode": row.zscore_mode,
                    "zscore_min_periods": row.zscore_min_periods,
                    "information_set_classification": "measured_data_vintage",
                    "retrieved_at": retrieved_at,
                }
            )
    return (
        pd.DataFrame(results, columns=POINT_IN_TIME_COLUMNS)
        .sort_values(["information_date", "model_id"])
        .reset_index(drop=True)
    )


def compare_point_in_time_to_current(
    point_in_time: pd.DataFrame,
    current_ogli: pd.DataFrame,
) -> pd.DataFrame:
    """Compare vintage and current-vintage calculations at the same observation date."""
    pit_required = {
        "information_date",
        "signal_observation_date",
        "model_id",
        "vintage_ogli",
        "vintage_momentum_score",
    }
    current_required = {"date", "model_id", "ogli", "momentum_score", "regime"}
    missing_pit = sorted(pit_required - set(point_in_time.columns))
    missing_current = sorted(current_required - set(current_ogli.columns))
    if missing_pit:
        raise PointInTimeError(f"Point-in-time results are missing: {', '.join(missing_pit)}")
    if missing_current:
        raise PointInTimeError(f"Current OGLI results are missing: {', '.join(missing_current)}")
    if point_in_time.empty or current_ogli.empty:
        raise PointInTimeError("Point-in-time comparison inputs cannot be empty")

    current = current_ogli[["date", "model_id", "ogli", "momentum_score", "regime"]].rename(
        columns={
            "date": "signal_observation_date",
            "ogli": "current_ogli",
            "momentum_score": "current_momentum_score",
            "regime": "current_regime",
        }
    )
    result = point_in_time.merge(
        current,
        on=["signal_observation_date", "model_id"],
        how="left",
        validate="many_to_one",
    )
    if result["current_ogli"].isna().any():
        missing_rows = result.loc[
            result["current_ogli"].isna(), ["signal_observation_date", "model_id"]
        ]
        example = missing_rows.iloc[0]
        raise PointInTimeError(
            "Current-vintage OGLI lacks an exact comparison for "
            f"{example['model_id']} on {pd.Timestamp(example['signal_observation_date']).date()}"
        )
    result["ogli_revision"] = result["current_ogli"] - result["vintage_ogli"]
    result["momentum_revision"] = (
        result["current_momentum_score"] - result["vintage_momentum_score"]
    )
    result["comparison_policy"] = "same_observation_date"
    return result.sort_values(["information_date", "model_id"]).reset_index(drop=True)


def _coerce_timestamp(value: str | date, label: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value).normalize()
    except (TypeError, ValueError) as exc:
        raise PointInTimeError(f"{label} must be an ISO date") from exc
    if pd.isna(timestamp):
        raise PointInTimeError(f"{label} must be an ISO date")
    return timestamp
