"""Experimental Open Global Liquidity Index statistical transformation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from open_global_liquidity.config import OGLIConfig, RegimeThreshold
from open_global_liquidity.transforms.normalize import ZScoreMode, historical_zscore


class OGLICalculationError(ValueError):
    """Raised when model momentum cannot support the configured OGLI calculation."""


def classify_ogli(value: float, regimes: tuple[RegimeThreshold, ...]) -> str | None:
    """Map a bounded OGLI value to the first inclusive configured upper threshold."""
    if pd.isna(value):
        return None
    if value < 0 or value > 100:
        raise OGLICalculationError("OGLI regime classification requires a value from 0 to 100")
    return next(regime.label for regime in regimes if value <= regime.max_value)


def momentum_to_ogli(scores: pd.Series) -> pd.Series:
    """Map z-like momentum scores through the standard normal CDF onto 0-100."""
    numeric = pd.to_numeric(scores, errors="coerce").astype(float)
    mapped = np.where(numeric.notna(), 100 * norm.cdf(numeric), np.nan)
    return pd.Series(mapped, index=scores.index, dtype=float).clip(0, 100)


def calculate_ogli(
    momentum: pd.DataFrame,
    config: OGLIConfig,
    *,
    mode: ZScoreMode | None = None,
) -> pd.DataFrame:
    """Calculate model-specific momentum scores and OGLI values.

    Each configured growth rate is standardized independently within its liquidity model. The
    weighted score is then mapped through ``100 * standard_normal_cdf(score)``. This preserves the
    interpretation of 50 as statistically neutral and does not force historical extremes to zero
    or 100. It is an independent OGLI method, not CrossBorder Capital's proprietary GLI.
    """
    required = {"date", "model_id", "growth_3m_annualized", "growth_12m_yoy"}
    missing = sorted(required - set(momentum.columns))
    if missing:
        raise OGLICalculationError(f"Momentum data is missing columns: {', '.join(missing)}")
    if momentum.empty:
        raise OGLICalculationError("Momentum data contains no observations")
    if momentum.duplicated(["date", "model_id"]).any():
        raise OGLICalculationError("Momentum data contains duplicate date/model observations")

    selected_mode: ZScoreMode = mode or config.normalization.default_mode  # type: ignore[assignment]
    result = momentum.sort_values(["model_id", "date"]).reset_index(drop=True).copy()
    z_columns: list[str] = []
    for growth_column in config.momentum_weights:
        z_column = f"z_{growth_column}"
        result[z_column] = result.groupby("model_id", sort=False)[growth_column].transform(
            lambda values: historical_zscore(
                values,
                mode=selected_mode,
                min_periods=config.normalization.min_periods,
            )
        )
        z_columns.append(z_column)

    weighted = pd.DataFrame(
        {
            z_column: result[z_column] * config.momentum_weights[growth_column]
            for growth_column, z_column in zip(config.momentum_weights, z_columns, strict=True)
        }
    )
    result["momentum_score"] = weighted.sum(axis=1, min_count=len(weighted.columns))
    result["ogli"] = momentum_to_ogli(result["momentum_score"])
    result["regime"] = result["ogli"].map(lambda value: classify_ogli(value, config.regimes))
    result["zscore_mode"] = selected_mode
    result["zscore_min_periods"] = config.normalization.min_periods
    result["ogli_classification"] = config.classification
    result["weight_classification"] = "model_assumption"
    return result
