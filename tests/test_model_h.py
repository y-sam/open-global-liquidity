from pathlib import Path

import pytest

from open_global_liquidity.models.model_h import (
    ModelHPreregistrationError,
    load_model_h_preregistration,
)


def test_loads_frozen_model_h_preregistration() -> None:
    path = Path(__file__).resolve().parents[1] / "config" / "model_h_preregistration.yaml"
    spec = load_model_h_preregistration(path)

    assert spec.status == "preregistered_not_calculated"
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
