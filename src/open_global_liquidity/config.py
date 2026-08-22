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
