"""Validated preregistration for the unimplemented broader Global Model H."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


class ModelHPreregistrationError(ValueError):
    """Raised when the Model H preregistration is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class ModelHPillar:
    """One economically defined input pillar and its assumed aggregation weight."""

    model_id: str
    weight: float
    role: str


@dataclass(frozen=True)
class ModelHPreregistration:
    """Frozen design contract; this object deliberately contains no calculate method."""

    name: str
    status: str
    frozen_on: pd.Timestamp
    canonical_frequency: str
    pillars: tuple[ModelHPillar, ...]
    score_formula: str
    index_formula: str
    prospective_start: pd.Timestamp
    promotion_rule: str
    research_boundary: str


def load_model_h_preregistration(path: Path) -> ModelHPreregistration:
    """Load and validate the frozen Model H design without calculating an index."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        pillar_items = raw["pillars"]
        aggregation = raw["aggregation"]
        evaluation = raw["evaluation"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise ModelHPreregistrationError(f"Could not load Model H preregistration: {exc}") from exc

    if (
        raw.get("classification") != "model_assumption"
        or raw.get("status") != "preregistered_not_calculated"
        or raw.get("calibrated_parameters") != {}
        or raw.get("canonical_frequency") != "quarter_end"
        or not isinstance(pillar_items, dict)
    ):
        raise ModelHPreregistrationError("Model H preregistration metadata is invalid")

    pillars = tuple(
        ModelHPillar(model_id=str(model_id), weight=float(item["weight"]), role=str(item["role"]))
        for model_id, item in pillar_items.items()
    )
    expected = {"global_model_g", "offshore_dollar_credit", "us_private_liquidity"}
    if {pillar.model_id for pillar in pillars} != expected:
        raise ModelHPreregistrationError("Model H must contain the three preregistered pillars")
    if (
        any(pillar.weight <= 0 for pillar in pillars)
        or abs(sum(pillar.weight for pillar in pillars) - 1.0) > 1e-9
    ):
        raise ModelHPreregistrationError("Model H pillar weights must be positive and sum to one")
    if evaluation.get("historical_results_label") != "post_specification_descriptive":
        raise ModelHPreregistrationError("Historical Model H results must remain descriptive")

    return ModelHPreregistration(
        name=str(raw["name"]),
        status=str(raw["status"]),
        frozen_on=pd.Timestamp(raw["frozen_on"]),
        canonical_frequency=str(raw["canonical_frequency"]),
        pillars=pillars,
        score_formula=str(aggregation["score_formula"]),
        index_formula=str(aggregation["index_formula"]),
        prospective_start=pd.Timestamp(evaluation["prospective_start"]),
        promotion_rule=str(evaluation["promotion_rule"]),
        research_boundary=str(raw["research_boundary"]),
    )
