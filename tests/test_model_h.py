from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.models.model_h import (
    ModelHPreregistrationError,
    calculate_model_h,
    load_model_h_preregistration,
)


def test_loads_frozen_model_h_preregistration() -> None:
    path = Path(__file__).resolve().parents[1] / "config" / "model_h_preregistration.yaml"
    spec = load_model_h_preregistration(path)

    assert spec.status == "preregistered_calculated_descriptive"
    assert spec.canonical_frequency == "quarter_end"
    assert spec.frozen_on.date().isoformat() == "2026-09-04"
    assert spec.prospective_start > spec.frozen_on
    assert sum(pillar.weight for pillar in spec.pillars) == pytest.approx(1.0)
    assert {pillar.model_id for pillar in spec.pillars} == {
        "global_model_g",
        "offshore_dollar_credit",
        "us_private_liquidity",
    }


def test_rejects_calibrated_model_h_parameters(tmp_path: Path) -> None:
    path = tmp_path / "model_h.yaml"
    path.write_text(
        """
classification: model_assumption
status: preregistered_not_calculated
canonical_frequency: quarter_end
pillars: {}
aggregation: {}
evaluation: {}
calibrated_parameters: {bitcoin_weight: 0.5}
""",
        encoding="utf-8",
    )

    with pytest.raises(ModelHPreregistrationError):
        load_model_h_preregistration(path)


def test_calculates_equal_weight_model_h_without_partial_rows() -> None:
    path = Path(__file__).resolve().parents[1] / "config" / "model_h_preregistration.yaml"
    spec = load_model_h_preregistration(path)
    dates = pd.date_range("2018-03-31", periods=24, freq="QE")
    global_model = pd.DataFrame({"date": dates, "global_cb_momentum_score": [1.0] * 24})
    offshore = pd.DataFrame(
        {
            "date": dates,
            "momentum_score": [2.0] * 24,
            "signal_available_date": dates + pd.offsets.MonthEnd(4),
        }
    )
    private = pd.DataFrame(
        {
            "date": dates,
            "private_liquidity_momentum": [3.0] * 24,
            "signal_available_date": dates + pd.offsets.MonthEnd(3),
        }
    )
    result = calculate_model_h(global_model, offshore, private, spec)
    assert result["model_h_momentum_score"].eq(2.0).all()
    assert (
        result[
            [
                "contribution_global_model_g",
                "contribution_offshore_dollar_credit",
                "contribution_us_private_liquidity",
            ]
        ]
        .sum(axis=1)
        .eq(result["model_h_momentum_score"])
        .all()
    )
    assert result["result_status"].eq("post_specification_descriptive").all()
    assert result["signal_available_date"].equals(offshore["signal_available_date"])
