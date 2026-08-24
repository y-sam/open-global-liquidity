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
class OGLINormalizationConfig:
    """Historical standardization policy for the experimental OGLI."""

    classification: str
    default_mode: str
    min_periods: int


@dataclass(frozen=True, slots=True)
class RegimeThreshold:
    """Inclusive upper boundary and display label for one OGLI regime."""

    label: str
    max_value: float


@dataclass(frozen=True, slots=True)
class OGLIConfig:
    """Assumptions and statistical transformations used by OGLI."""

    classification: str
    description: str
    normalization: OGLINormalizationConfig
    momentum_weights: dict[str, float]
    regime_classification: str
    regimes: tuple[RegimeThreshold, ...]


@dataclass(frozen=True, slots=True)
class MarketAlignmentConfig:
    """Explicit policy for aligning daily market closes to canonical Wednesdays."""

    classification: str
    canonical_frequency: str
    observation_day: str
    daily_asof_components: tuple[str, ...]
    daily_asof_max_staleness_days: int
    missing_policy: str


@dataclass(frozen=True, slots=True)
class MarketAnalysisConfig:
    """Configured statistical choices for liquidity-versus-market research."""

    classification: str
    liquidity_signal: str
    publication_lag_policy: str
    signal_availability_lag_weeks: int
    forward_horizons_weeks: tuple[int, ...]
    correlation_min_periods: int
    non_overlapping_min_periods: int
    confidence_level: float
    rolling_window_weeks: int
    rolling_min_periods: int
    description: str


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Weekly alignment policy and competing liquidity definitions."""

    alignment: WeeklyAlignmentConfig
    models: tuple[LiquidityModelDefinition, ...]
    ogli: OGLIConfig
    market_alignment: MarketAlignmentConfig
    market_analysis: MarketAnalysisConfig


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
    ogli = _parse_ogli_config(payload.get("ogli"))
    market_alignment = _parse_market_alignment(payload.get("market_alignment"))
    market_analysis = _parse_market_analysis(payload.get("market_analysis"))
    return ModelConfig(
        alignment=alignment,
        models=tuple(models),
        ogli=ogli,
        market_alignment=market_alignment,
        market_analysis=market_analysis,
    )


def _parse_ogli_config(raw: Any) -> OGLIConfig:
    if not isinstance(raw, dict):
        raise ConfigurationError("ogli must be a mapping")
    if raw.get("classification") != "statistical_transformation":
        raise ConfigurationError("ogli must be classified as statistical_transformation")

    normalization = raw.get("normalization")
    if not isinstance(normalization, dict):
        raise ConfigurationError("ogli.normalization must be a mapping")
    if normalization.get("classification") != "statistical_transformation":
        raise ConfigurationError(
            "ogli.normalization must be classified as statistical_transformation"
        )
    mode = str(normalization.get("default_mode"))
    if mode not in {"expanding", "full_sample"}:
        raise ConfigurationError("ogli.normalization.default_mode must be expanding or full_sample")
    try:
        min_periods = int(normalization["min_periods"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError("ogli.normalization.min_periods must be an integer") from exc
    if min_periods < 2:
        raise ConfigurationError("ogli.normalization.min_periods must be at least 2")

    raw_weights = raw.get("momentum_weights")
    if not isinstance(raw_weights, dict):
        raise ConfigurationError("ogli.momentum_weights must be a mapping")
    if raw_weights.get("classification") != "model_assumption":
        raise ConfigurationError("ogli.momentum_weights must be classified as model_assumption")
    expected_weights = {"growth_3m_annualized", "growth_12m_yoy"}
    weight_keys = set(raw_weights) - {"classification"}
    if weight_keys != expected_weights:
        raise ConfigurationError(
            "ogli.momentum_weights must define growth_3m_annualized and growth_12m_yoy"
        )
    try:
        weights = {key: float(raw_weights[key]) for key in sorted(expected_weights)}
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("ogli momentum weights must be numeric") from exc
    if any(weight < 0 for weight in weights.values()):
        raise ConfigurationError("ogli momentum weights cannot be negative")
    if abs(sum(weights.values()) - 1.0) > 1e-12:
        raise ConfigurationError("ogli momentum weights must sum to 1.0")

    raw_regimes = raw.get("regimes")
    if not isinstance(raw_regimes, dict):
        raise ConfigurationError("ogli.regimes must be a mapping")
    if raw_regimes.get("classification") != "model_assumption":
        raise ConfigurationError("ogli.regimes must be classified as model_assumption")
    raw_thresholds = raw_regimes.get("thresholds")
    if not isinstance(raw_thresholds, list) or not raw_thresholds:
        raise ConfigurationError("ogli.regimes.thresholds must be a non-empty list")
    regimes: list[RegimeThreshold] = []
    for item in raw_thresholds:
        if not isinstance(item, dict) or set(item) != {"label", "max"}:
            raise ConfigurationError("each OGLI regime must define label and max")
        regimes.append(RegimeThreshold(label=str(item["label"]), max_value=float(item["max"])))
    boundaries = [regime.max_value for regime in regimes]
    if boundaries != sorted(boundaries) or len(set(boundaries)) != len(boundaries):
        raise ConfigurationError("OGLI regime maxima must be strictly increasing")
    if boundaries[-1] != 100.0:
        raise ConfigurationError("the final OGLI regime maximum must be 100")

    return OGLIConfig(
        classification=str(raw["classification"]),
        description=str(raw.get("description", "")),
        normalization=OGLINormalizationConfig(
            classification=str(normalization["classification"]),
            default_mode=mode,
            min_periods=min_periods,
        ),
        momentum_weights=weights,
        regime_classification=str(raw_regimes["classification"]),
        regimes=tuple(regimes),
    )


def _parse_market_alignment(raw: Any) -> MarketAlignmentConfig:
    if not isinstance(raw, dict):
        raise ConfigurationError("market_alignment must be a mapping")
    required = {
        "classification",
        "canonical_frequency",
        "observation_day",
        "daily_asof_components",
        "daily_asof_max_staleness_days",
        "missing_policy",
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise ConfigurationError(f"market_alignment is missing fields: {', '.join(missing)}")
    if raw["classification"] != "model_assumption":
        raise ConfigurationError("market_alignment must be classified as model_assumption")
    if raw["canonical_frequency"] != "W-WED":
        raise ConfigurationError("v0.1 market canonical_frequency must be W-WED")
    if raw["missing_policy"] != "latest_prior_close":
        raise ConfigurationError("v0.1 market missing_policy must be latest_prior_close")
    components = raw["daily_asof_components"]
    if not isinstance(components, list) or not all(isinstance(item, str) for item in components):
        raise ConfigurationError("market daily_asof_components must be a list of component names")
    try:
        max_staleness = int(raw["daily_asof_max_staleness_days"])
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("market daily_asof_max_staleness_days must be an integer") from exc
    if max_staleness < 0:
        raise ConfigurationError("market daily_asof_max_staleness_days cannot be negative")
    return MarketAlignmentConfig(
        classification=str(raw["classification"]),
        canonical_frequency=str(raw["canonical_frequency"]),
        observation_day=str(raw["observation_day"]),
        daily_asof_components=tuple(components),
        daily_asof_max_staleness_days=max_staleness,
        missing_policy=str(raw["missing_policy"]),
    )


def _parse_market_analysis(raw: Any) -> MarketAnalysisConfig:
    if not isinstance(raw, dict):
        raise ConfigurationError("market_analysis must be a mapping")
    required = {
        "classification",
        "liquidity_signal",
        "publication_lag_policy",
        "signal_availability_lag_weeks",
        "forward_horizons_weeks",
        "correlation_min_periods",
        "non_overlapping_min_periods",
        "confidence_level",
        "rolling_window_weeks",
        "rolling_min_periods",
        "description",
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise ConfigurationError(f"market_analysis is missing fields: {', '.join(missing)}")
    if raw["classification"] != "statistical_transformation":
        raise ConfigurationError("market_analysis must be classified as statistical_transformation")
    if raw["publication_lag_policy"] != "observation_and_available_information":
        raise ConfigurationError(
            "market publication_lag_policy must be observation_and_available_information"
        )
    raw_horizons = raw["forward_horizons_weeks"]
    if not isinstance(raw_horizons, list):
        raise ConfigurationError("market forward_horizons_weeks must be a list")
    try:
        horizons = tuple(int(item) for item in raw_horizons)
        availability_lag = int(raw["signal_availability_lag_weeks"])
        correlation_min = int(raw["correlation_min_periods"])
        non_overlapping_min = int(raw["non_overlapping_min_periods"])
        confidence_level = float(raw["confidence_level"])
        rolling_window = int(raw["rolling_window_weeks"])
        rolling_min = int(raw["rolling_min_periods"])
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("market analysis periods must be integers") from exc
    if not horizons or horizons[0] != 0 or any(item < 0 for item in horizons):
        raise ConfigurationError("market horizons must start at zero and cannot be negative")
    if tuple(sorted(set(horizons))) != horizons:
        raise ConfigurationError("market horizons must be unique and increasing")
    if availability_lag < 0:
        raise ConfigurationError("signal_availability_lag_weeks cannot be negative")
    if correlation_min < 2 or non_overlapping_min < 2:
        raise ConfigurationError("market correlation minimum periods must be at least 2")
    if rolling_min < 2 or rolling_window < rolling_min:
        raise ConfigurationError("market correlation history settings are inconsistent")
    if not 0 < confidence_level < 1:
        raise ConfigurationError("market confidence_level must be between 0 and 1")
    return MarketAnalysisConfig(
        classification=str(raw["classification"]),
        liquidity_signal=str(raw["liquidity_signal"]),
        publication_lag_policy=str(raw["publication_lag_policy"]),
        signal_availability_lag_weeks=availability_lag,
        forward_horizons_weeks=horizons,
        correlation_min_periods=correlation_min,
        non_overlapping_min_periods=non_overlapping_min,
        confidence_level=confidence_level,
        rolling_window_weeks=rolling_window,
        rolling_min_periods=rolling_min,
        description=str(raw["description"]),
    )


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
