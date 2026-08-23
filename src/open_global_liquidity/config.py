"""Validated loading of measured-series configuration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when project configuration is missing or malformed."""


@dataclass(frozen=True, slots=True)
class SeriesDefinition:
    """Auditable metadata for one public source series."""

    country: str
    group: str
    name: str
    classification: str
    provider: str
    series_id: str
    component: str
    title: str
    description: str
    unit: str
    frequency: str
    seasonal_adjustment: str
    start: date
    source: str
    source_url: str


@dataclass(frozen=True, slots=True)
class WeeklyAlignmentConfig:
    """Explicit research assumptions for canonical weekly alignment."""

    classification: str
    canonical_frequency: str
    observation_day: str
    output_unit: str
    daily_asof_components: tuple[str, ...]
    daily_asof_max_staleness_days: int
    weekly_missing_policy: str


@dataclass(frozen=True, slots=True)
class LiquidityModelDefinition:
    """One transparent, configurable linear liquidity model."""

    model_id: str
    name: str
    classification: str
    formula: str
    description: str
    terms: dict[str, float]


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Weekly alignment policy and competing liquidity definitions."""

    alignment: WeeklyAlignmentConfig
    models: tuple[LiquidityModelDefinition, ...]


_REQUIRED_FIELDS = {
    "classification",
    "provider",
    "series_id",
    "component",
    "title",
    "description",
    "unit",
    "frequency",
    "seasonal_adjustment",
    "start",
    "source",
    "source_url",
}


def load_series_config(path: Path) -> list[SeriesDefinition]:
    """Load a country/group/name YAML hierarchy into typed series definitions."""
    if not path.is_file():
        raise ConfigurationError(f"Series configuration not found: {path}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(payload, dict) or not payload:
        raise ConfigurationError(f"Series configuration must be a non-empty mapping: {path}")

    definitions: list[SeriesDefinition] = []
    for country, groups in payload.items():
        if not isinstance(groups, dict):
            raise ConfigurationError(f"Country {country!r} must contain series groups")
        for group, named_series in groups.items():
            if not isinstance(named_series, dict):
                raise ConfigurationError(f"Series group {country}.{group} must be a mapping")
            for name, raw in named_series.items():
                definitions.append(_parse_definition(str(country), str(group), str(name), raw))

    return definitions


def load_model_config(path: Path) -> ModelConfig:
    """Load and validate weekly alignment and liquidity-model assumptions."""
    if not path.is_file():
        raise ConfigurationError(f"Model configuration not found: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Model configuration must be a mapping: {path}")

    raw_alignment = payload.get("weekly_alignment")
    if not isinstance(raw_alignment, dict):
        raise ConfigurationError("weekly_alignment must be a mapping")
    required_alignment = {
        "classification",
        "canonical_frequency",
        "observation_day",
        "output_unit",
        "daily_asof_components",
        "daily_asof_max_staleness_days",
        "weekly_missing_policy",
    }
    missing_alignment = sorted(required_alignment - raw_alignment.keys())
    if missing_alignment:
        raise ConfigurationError(
            f"weekly_alignment is missing fields: {', '.join(missing_alignment)}"
        )
    if raw_alignment["classification"] != "model_assumption":
        raise ConfigurationError("weekly_alignment must be classified as model_assumption")
    if raw_alignment["canonical_frequency"] != "W-WED":
        raise ConfigurationError("v0.1 canonical_frequency must be W-WED")
    if raw_alignment["weekly_missing_policy"] != "exact_only":
        raise ConfigurationError("v0.1 weekly_missing_policy must be exact_only")
    daily_components = raw_alignment["daily_asof_components"]
    if not isinstance(daily_components, list) or not all(
        isinstance(component, str) for component in daily_components
    ):
        raise ConfigurationError("daily_asof_components must be a list of component names")
    try:
        max_staleness = int(raw_alignment["daily_asof_max_staleness_days"])
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("daily_asof_max_staleness_days must be an integer") from exc
    if max_staleness < 0:
        raise ConfigurationError("daily_asof_max_staleness_days cannot be negative")

    alignment = WeeklyAlignmentConfig(
        classification=str(raw_alignment["classification"]),
        canonical_frequency=str(raw_alignment["canonical_frequency"]),
        observation_day=str(raw_alignment["observation_day"]),
        output_unit=str(raw_alignment["output_unit"]),
        daily_asof_components=tuple(daily_components),
        daily_asof_max_staleness_days=max_staleness,
        weekly_missing_policy=str(raw_alignment["weekly_missing_policy"]),
    )

    raw_models = payload.get("liquidity_models")
    if not isinstance(raw_models, dict) or not raw_models:
        raise ConfigurationError("liquidity_models must be a non-empty mapping")
    models: list[LiquidityModelDefinition] = []
    required_model = {"name", "classification", "formula", "description", "terms"}
    for model_id, raw_model in raw_models.items():
        if not isinstance(raw_model, dict):
            raise ConfigurationError(f"Liquidity model {model_id} must be a mapping")
        missing_model = sorted(required_model - raw_model.keys())
        if missing_model:
            raise ConfigurationError(
                f"Liquidity model {model_id} is missing fields: {', '.join(missing_model)}"
            )
        if raw_model["classification"] != "model_assumption":
            raise ConfigurationError(
                f"Liquidity model {model_id} must be classified as model_assumption"
            )
        raw_terms = raw_model["terms"]
        if not isinstance(raw_terms, dict) or not raw_terms:
            raise ConfigurationError(f"Liquidity model {model_id} terms must be a mapping")
        try:
            terms = {str(component): float(weight) for component, weight in raw_terms.items()}
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                f"Liquidity model {model_id} term weights must be numeric"
            ) from exc
        models.append(
            LiquidityModelDefinition(
                model_id=str(model_id),
                name=str(raw_model["name"]),
                classification=str(raw_model["classification"]),
                formula=str(raw_model["formula"]),
                description=str(raw_model["description"]),
                terms=terms,
            )
        )
    return ModelConfig(alignment=alignment, models=tuple(models))


def _parse_definition(country: str, group: str, name: str, raw: Any) -> SeriesDefinition:
    if not isinstance(raw, dict):
        raise ConfigurationError(f"Series {country}.{group}.{name} must be a mapping")

    missing = sorted(_REQUIRED_FIELDS - raw.keys())
    if missing:
        raise ConfigurationError(
            f"Series {country}.{group}.{name} is missing fields: {', '.join(missing)}"
        )
    if raw["classification"] != "measured_data":
        raise ConfigurationError(
            f"Source series {country}.{group}.{name} must be classified as measured_data"
        )

    try:
        start = date.fromisoformat(str(raw["start"]))
    except ValueError as exc:
        raise ConfigurationError(
            f"Series {country}.{group}.{name} has invalid ISO start date: {raw['start']!r}"
        ) from exc

    values = {field: str(raw[field]) for field in _REQUIRED_FIELDS if field != "start"}
    return SeriesDefinition(country=country, group=group, name=name, start=start, **values)
