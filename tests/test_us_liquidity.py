from pathlib import Path

import pandas as pd

from open_global_liquidity.config import load_model_config
from open_global_liquidity.models.us_liquidity import calculate_us_liquidity_models


def _aligned(value_by_component: dict[str, float | None]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-03")] * len(value_by_component),
            "component": list(value_by_component),
            "value": list(value_by_component.values()),
            "unit": ["Millions of U.S. Dollars"] * len(value_by_component),
            "frequency": ["Weekly, As of Wednesday"] * len(value_by_component),
        }
    )


def test_three_us_liquidity_model_formulas() -> None:
    config = load_model_config(Path("config/model.yaml"))
    source = _aligned(
        {
            "fed_assets": 8_000_000.0,
            "treasury_general_account": 500_000.0,
            "overnight_reverse_repo": 1_000_000.0,
            "reserve_balances": 3_000_000.0,
        }
    )

    result = calculate_us_liquidity_models(source, config.models).set_index("model_id")

    assert result.loc["model_a", "value"] == 8_000_000.0
    assert result.loc["model_b", "value"] == 6_500_000.0
    assert result.loc["model_c", "value"] == 3_000_000.0


def test_model_is_missing_when_any_required_input_is_missing() -> None:
    config = load_model_config(Path("config/model.yaml"))
    source = _aligned(
        {
            "fed_assets": 8_000_000.0,
            "treasury_general_account": 500_000.0,
            "overnight_reverse_repo": None,
            "reserve_balances": 3_000_000.0,
        }
    )

    result = calculate_us_liquidity_models(source, config.models).set_index("model_id")

    assert pd.isna(result.loc["model_b", "value"])
    assert not bool(result.loc["model_b", "is_complete"])
    assert result.loc["model_a", "value"] == 8_000_000.0
    assert result.loc["model_c", "value"] == 3_000_000.0
