"""Frozen specification and descriptive calculation for broader Global Model H."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from open_global_liquidity.models.ogli import momentum_to_ogli


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
    """Frozen design contract for the descriptive Model H calculation."""

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
        or raw.get("status") != "preregistered_calculated_descriptive"
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


def calculate_model_h(
    global_model: pd.DataFrame,
    offshore_dollar: pd.DataFrame,
    private_liquidity: pd.DataFrame,
    config: ModelHPreregistration,
) -> pd.DataFrame:
    """Calculate the frozen equal-weight quarterly challenger without fitting market outcomes.

    Global Model G is sampled at calendar quarter-end. The two slower pillars already have
    quarterly observation and assumed availability dates. A Model H reading becomes available
    only when all three inputs are available; no missing pillar is interpolated or reweighted.
    """
    required = {
        "global": {"date", "global_cb_momentum_score"},
        "offshore": {"date", "momentum_score", "signal_available_date"},
        "private": {"date", "private_liquidity_momentum", "signal_available_date"},
    }
    for name, (frame, columns) in zip(
        required,
        (
            (global_model, required["global"]),
            (offshore_dollar, required["offshore"]),
            (private_liquidity, required["private"]),
        ),
        strict=True,
    ):
        missing = columns - set(frame.columns)
        if missing:
            raise ModelHPreregistrationError(
                f"{name} input is missing: {', '.join(sorted(missing))}"
            )

    g = global_model.copy()
    g["date"] = pd.to_datetime(g["date"])
    g = g.loc[g["date"].dt.month.isin([3, 6, 9, 12]), ["date", "global_cb_momentum_score"]]
    g["global_available_date"] = g["date"] + pd.offsets.MonthEnd(2)
    o = (
        offshore_dollar[["date", "momentum_score", "signal_available_date"]]
        .copy()
        .rename(
            columns={
                "momentum_score": "offshore_dollar_momentum",
                "signal_available_date": "offshore_available_date",
            }
        )
    )
    p = (
        private_liquidity[["date", "private_liquidity_momentum", "signal_available_date"]]
        .copy()
        .rename(columns={"signal_available_date": "private_available_date"})
    )
    for frame in (o, p):
        frame["date"] = pd.to_datetime(frame["date"])
    result = g.merge(o, on="date", how="inner", validate="one_to_one").merge(
        p, on="date", how="inner", validate="one_to_one"
    )
    score_columns = {
        "global_model_g": "global_cb_momentum_score",
        "offshore_dollar_credit": "offshore_dollar_momentum",
        "us_private_liquidity": "private_liquidity_momentum",
    }
    result = result.dropna(subset=list(score_columns.values())).reset_index(drop=True)
    if len(result) < 20:
        raise ModelHPreregistrationError("Model H requires at least 20 complete quarterly readings")
    result["model_h_momentum_score"] = sum(
        result[score_columns[pillar.model_id]] * pillar.weight for pillar in config.pillars
    )
    result["model_h_index"] = momentum_to_ogli(result["model_h_momentum_score"])
    result["signal_available_date"] = result[
        ["global_available_date", "offshore_available_date", "private_available_date"]
    ].max(axis=1)
    result["model_id"] = "model_h"
    result["model_name"] = config.name
    result["result_status"] = "post_specification_descriptive"
    result["calibration_status"] = "not_calibrated"
    result["production_model"] = False
    return result
