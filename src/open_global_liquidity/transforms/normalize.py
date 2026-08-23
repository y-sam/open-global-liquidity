"""Historical standardization without implicit min-max rescaling."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

ZScoreMode = Literal["expanding", "full_sample"]


class NormalizationError(ValueError):
    """Raised when a requested historical normalization is invalid."""


def historical_zscore(
    values: pd.Series,
    *,
    mode: ZScoreMode = "expanding",
    min_periods: int = 104,
) -> pd.Series:
    """Standardize observations using expanding or full-sample population moments.

    Expanding mode uses only observations available through each row and is suitable for
    historical backtests. Full-sample mode uses the entire supplied sample and therefore embeds
    look-ahead; it is provided only for exploratory research. A zero standard deviation yields
    missing scores rather than a misleading neutral value.
    """
    if mode not in {"expanding", "full_sample"}:
        raise NormalizationError(f"Unsupported z-score mode: {mode}")
    if min_periods < 2:
        raise NormalizationError("min_periods must be at least 2")

    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    if mode == "expanding":
        moments = numeric.expanding(min_periods=min_periods)
        mean = moments.mean()
        std = moments.std(ddof=0)
        return ((numeric - mean) / std).where(std > 0)

    if numeric.count() < min_periods:
        return pd.Series(np.nan, index=numeric.index, dtype=float)
    std = numeric.std(ddof=0)
    if pd.isna(std) or std <= 0:
        return pd.Series(np.nan, index=numeric.index, dtype=float)
    return (numeric - numeric.mean()) / std
