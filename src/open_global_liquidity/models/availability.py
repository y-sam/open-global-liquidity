"""Availability and vintage-coverage registry for global model inputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


class AvailabilityRegistryError(ValueError):
    """Raised when the declared global availability registry is malformed."""


def load_global_availability_registry(path: Path) -> pd.DataFrame:
    """Load auditable timing assumptions without claiming reconstructed historical vintages."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        inputs = raw["inputs"]
        conclusion = raw["conclusion"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise AvailabilityRegistryError(
            f"Could not load global availability registry: {exc}"
        ) from exc
    if (
        raw.get("classification") != "model_assumption"
        or raw.get("calibrated_parameters") != {}
        or conclusion.get("genuine_point_in_time_global_model") is not False
        or conclusion.get("current_label") != "lag_adjusted_current_vintage"
        or not isinstance(inputs, dict)
        or not inputs
    ):
        raise AvailabilityRegistryError("Global availability registry is invalid")
    rows: list[dict[str, object]] = []
    for component, item in inputs.items():
        lag_months = int(item.get("conservative_lag_months", 0))
        lag_days = int(item.get("conservative_lag_days", 0))
        if (
            lag_months < 0
            or lag_days < 0
            or (lag_months == 0) == (lag_days == 0)
            or item.get("model_role") not in {"central_bank_asset", "fx_translation"}
        ):
            raise AvailabilityRegistryError(f"Availability entry is invalid: {component}")
        rows.append(
            {
                "component": str(component),
                "provider": str(item["provider"]),
                "source_family": str(item["source_family"]),
                "model_role": str(item["model_role"]),
                "availability_policy": str(item["availability_policy"]),
                "conservative_lag_months": lag_months,
                "conservative_lag_days": lag_days,
                "historical_release_calendar": str(item["historical_release_calendar"]),
                "historical_value_vintages": str(item["historical_value_vintages"]),
                "point_in_time_status": "lag_adjusted_current_vintage",
                "classification": "model_assumption",
                "registry_as_of": pd.Timestamp(raw["as_of"]),
            }
        )
    result = pd.DataFrame(rows).sort_values(["model_role", "component"]).reset_index(drop=True)
    if set(result["model_role"]) != {"central_bank_asset", "fx_translation"}:
        raise AvailabilityRegistryError("Registry must cover central-bank and FX model inputs")
    return result
