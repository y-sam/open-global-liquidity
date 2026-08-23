"""Transparent competing definitions of US liquidity."""

from __future__ import annotations

import pandas as pd

from open_global_liquidity.config import LiquidityModelDefinition


class LiquidityModelError(ValueError):
    """Raised when aligned inputs cannot support a configured liquidity model."""


def calculate_us_liquidity_models(
    aligned: pd.DataFrame, definitions: tuple[LiquidityModelDefinition, ...]
) -> pd.DataFrame:
    """Calculate configured linear models from aligned USD-million stock variables.

    Each formula is a transparent weighted sum from ``config/model.yaml``. A model value remains
    missing when any required component is unavailable, preventing silent partial calculations.
    These are OGLI research assumptions, not CrossBorder Capital's proprietary methodology.
    """
    required = {"date", "component", "value", "unit", "frequency"}
    missing = sorted(required - set(aligned.columns))
    if missing:
        raise LiquidityModelError(
            f"Liquidity model inputs are missing columns: {', '.join(missing)}"
        )
    if aligned.empty:
        raise LiquidityModelError("Liquidity model inputs contain no observations")
    if set(aligned["unit"].dropna()) != {"Millions of U.S. Dollars"}:
        raise LiquidityModelError("Liquidity model inputs must use Millions of U.S. Dollars")
    if aligned.duplicated(["date", "component"]).any():
        raise LiquidityModelError("Liquidity model inputs contain duplicate date/components")

    pivoted = aligned.pivot(index="date", columns="component", values="value").sort_index()
    frames: list[pd.DataFrame] = []
    for definition in definitions:
        missing_components = sorted(set(definition.terms) - set(pivoted.columns))
        if missing_components:
            raise LiquidityModelError(
                f"Model {definition.model_id} is missing components: "
                + ", ".join(missing_components)
            )
        weighted = pivoted[list(definition.terms)].mul(pd.Series(definition.terms))
        values = weighted.sum(axis=1, min_count=len(definition.terms))
        model = values.rename("value").reset_index()
        model["model_id"] = definition.model_id
        model["model_name"] = definition.name
        model["unit"] = "Millions of U.S. Dollars"
        model["frequency"] = "Weekly, As of Wednesday"
        model["classification"] = definition.classification
        model["formula"] = definition.formula
        model["description"] = definition.description
        model["is_complete"] = model["value"].notna()
        frames.append(model)

    columns = [
        "date",
        "model_id",
        "model_name",
        "value",
        "unit",
        "frequency",
        "classification",
        "formula",
        "description",
        "is_complete",
    ]
    return (
        pd.concat(frames, ignore_index=True)[columns]
        .sort_values(["date", "model_id"])
        .reset_index(drop=True)
    )
