"""Shared data contracts for provider observations."""

from __future__ import annotations

import pandas as pd

STANDARD_COLUMNS = [
    "date",
    "country",
    "provider",
    "series_id",
    "component",
    "value",
    "unit",
    "frequency",
    "retrieved_at",
]


class DataValidationError(ValueError):
    """Raised when provider data does not satisfy the internal contract."""


def validate_standardized_frame(frame: pd.DataFrame) -> None:
    """Fail fast when a standardized provider frame is empty or malformed."""
    missing = [column for column in STANDARD_COLUMNS if column not in frame.columns]
    if missing:
        raise DataValidationError(f"Standardized data is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise DataValidationError("Standardized data contains no observations")
    if frame["date"].isna().any():
        raise DataValidationError("Standardized data contains invalid dates")
    if frame["value"].notna().sum() == 0:
        raise DataValidationError("Standardized data contains no numeric values")
