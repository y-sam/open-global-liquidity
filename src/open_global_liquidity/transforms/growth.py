"""Momentum transformations for canonical weekly liquidity model levels."""

from __future__ import annotations

import numpy as np
import pandas as pd


class GrowthCalculationError(ValueError):
    """Raised when model levels cannot support deterministic momentum calculations."""


WEEK_LAGS = {
    "change_1m": 4,
    "change_3m": 13,
    "change_6m": 26,
    "change_12m": 52,
}


def calculate_liquidity_momentum(models: pd.DataFrame) -> pd.DataFrame:
    """Add transparent changes and growth rates to weekly model levels.

    Month labels are fixed weekly approximations: 1m=4 weeks, 3m=13 weeks, 6m=26 weeks,
    and 12m=52 weeks. Changes are absolute differences in the model's level unit. Three-month
    annualized growth is ``(L_t / L_t-13w) ** (52/13) - 1``; year-over-year growth is
    ``L_t / L_t-52w - 1``. Ratios are missing when either endpoint is non-positive because the
    compounded-growth interpretation would not be economically meaningful.
    """
    required = {"date", "model_id", "model_name", "value"}
    missing = sorted(required - set(models.columns))
    if missing:
        raise GrowthCalculationError(f"Model levels are missing columns: {', '.join(missing)}")
    if models.empty:
        raise GrowthCalculationError("Model levels contain no observations")
    if models.duplicated(["date", "model_id"]).any():
        raise GrowthCalculationError("Model levels contain duplicate date/model observations")

    result = models.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.sort_values(["model_id", "date"]).reset_index(drop=True)
    grouped = result.groupby("model_id", sort=False)["value"]
    for column, periods in WEEK_LAGS.items():
        result[column] = result["value"] - grouped.shift(periods)

    lag_3m = grouped.shift(13)
    lag_12m = grouped.shift(52)
    valid_3m = (result["value"] > 0) & (lag_3m > 0)
    valid_12m = (result["value"] > 0) & (lag_12m > 0)
    result["growth_3m_annualized"] = np.where(
        valid_3m,
        (result["value"] / lag_3m) ** (52 / 13) - 1,
        np.nan,
    )
    result["growth_12m_yoy"] = np.where(
        valid_12m,
        result["value"] / lag_12m - 1,
        np.nan,
    )
    result["momentum_classification"] = "statistical_transformation"
    return result
