"""Explicit monetary-unit conversions."""

from __future__ import annotations

import pandas as pd


class UnitConversionError(ValueError):
    """Raised when a source unit cannot be converted without guessing."""


_TO_USD_MILLIONS = {
    "Millions of U.S. Dollars": 1.0,
    "Billions of U.S. Dollars": 1_000.0,
}


def convert_to_usd_millions(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert supported nominal dollar stocks to a common USD-millions unit.

    The conversion changes scale only: values reported in billions are multiplied by 1,000 and
    values reported in millions are unchanged. It applies no deflation, FX conversion, smoothing,
    or economic weighting.
    """
    required = {"value", "unit"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise UnitConversionError(f"Unit conversion is missing columns: {', '.join(missing)}")
    unsupported = sorted(set(frame["unit"].dropna()) - _TO_USD_MILLIONS.keys())
    if unsupported:
        raise UnitConversionError("Unsupported monetary units: " + ", ".join(unsupported))

    result = frame.copy()
    result["source_unit"] = result["unit"]
    result["value"] = result["value"] * result["unit"].map(_TO_USD_MILLIONS)
    result["unit"] = "Millions of U.S. Dollars"
    return result
