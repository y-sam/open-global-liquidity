"""Measured macro context series kept separate from OGLI inputs."""

from __future__ import annotations

import pandas as pd


class MacroContextError(ValueError):
    """Raised when measured context data cannot support the requested transformation."""


def build_us_macro_context(weekly_context: pd.DataFrame) -> pd.DataFrame:
    """Create a weekly context table and the transparent 10y-minus-2y yield-curve slope.

    Treasury yields and the broad dollar index remain measured levels. The yield-curve slope is a
    deterministic statistical transformation in percentage points. None of these columns enters a
    liquidity model, OGLI momentum, or OGLI normalization.
    """
    required = {"date", "component", "value"}
    missing = sorted(required - set(weekly_context.columns))
    if missing:
        raise MacroContextError("Macro context data is missing columns: " + ", ".join(missing))
    expected = {"treasury_yield_10y", "treasury_yield_2y", "broad_usd_index"}
    available = set(weekly_context["component"].unique())
    missing_components = sorted(expected - available)
    if missing_components:
        raise MacroContextError(
            "Macro context is missing components: " + ", ".join(missing_components)
        )
    if weekly_context.duplicated(["date", "component"]).any():
        raise MacroContextError("Macro context contains duplicate date/components")

    result = (
        weekly_context.pivot(index="date", columns="component", values="value")
        .reset_index()
        .rename_axis(columns=None)
    )
    result["yield_curve_10y_2y"] = result["treasury_yield_10y"] - result["treasury_yield_2y"]
    result["classification"] = "statistical_transformation"
    return (
        result[
            [
                "date",
                "treasury_yield_10y",
                "treasury_yield_2y",
                "yield_curve_10y_2y",
                "broad_usd_index",
                "classification",
            ]
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )
