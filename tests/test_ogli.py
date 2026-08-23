from pathlib import Path

import numpy as np
import pandas as pd

from open_global_liquidity.config import load_model_config
from open_global_liquidity.models.ogli import calculate_ogli, classify_ogli, momentum_to_ogli


def _momentum(length: int) -> pd.DataFrame:
    values = np.linspace(-0.2, 0.3, length)
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=length, freq="W-WED"),
            "model_id": "model_a",
            "growth_3m_annualized": values,
            "growth_12m_yoy": values * 0.7 + 0.02,
        }
    )


def test_normal_cdf_known_values() -> None:
    result = momentum_to_ogli(pd.Series([-2.0, -1.0, 0.0, 1.0, 2.0]))

    np.testing.assert_allclose(result, [2.275013, 15.865525, 50.0, 84.134475, 97.724987])


def test_composite_uses_configured_weights() -> None:
    config = load_model_config(Path("config/model.yaml"))
    result = calculate_ogli(_momentum(120), config.ogli, mode="full_sample")
    last = result.iloc[-1]

    expected = 0.6 * last["z_growth_3m_annualized"] + 0.4 * last["z_growth_12m_yoy"]
    assert np.isclose(last["momentum_score"], expected)
    assert np.isclose(last["ogli"], momentum_to_ogli(pd.Series([expected])).iloc[0])


def test_expanding_ogli_is_invariant_to_extreme_future_values() -> None:
    config = load_model_config(Path("config/model.yaml"))
    original = _momentum(140)
    future = _momentum(5)
    future["date"] = pd.date_range(
        original["date"].max() + pd.Timedelta(weeks=1), periods=5, freq="W-WED"
    )
    future["growth_3m_annualized"] = [10.0, -10.0, 20.0, -20.0, 100.0]
    future["growth_12m_yoy"] = [-50.0, 50.0, -100.0, 100.0, 500.0]

    before = calculate_ogli(original, config.ogli, mode="expanding")
    after = calculate_ogli(
        pd.concat([original, future], ignore_index=True), config.ogli, mode="expanding"
    )

    columns = [
        "z_growth_3m_annualized",
        "z_growth_12m_yoy",
        "momentum_score",
        "ogli",
    ]
    pd.testing.assert_frame_equal(before[columns], after.loc[: len(before) - 1, columns])


def test_regime_boundaries_are_inclusive_upper_limits() -> None:
    regimes = load_model_config(Path("config/model.yaml")).ogli.regimes

    assert classify_ogli(0, regimes) == "Strong contraction"
    assert classify_ogli(10, regimes) == "Strong contraction"
    assert classify_ogli(10.0001, regimes) == "Contraction"
    assert classify_ogli(45, regimes) == "Below normal"
    assert classify_ogli(50, regimes) == "Neutral"
    assert classify_ogli(90, regimes) == "Expansion"
    assert classify_ogli(100, regimes) == "Strong expansion"
