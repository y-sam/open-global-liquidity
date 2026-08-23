import numpy as np
import pandas as pd

from open_global_liquidity.analysis.lead_lag import (
    build_liquidity_market_comparison,
    calculate_market_forward_returns,
)


def test_market_returns_define_zero_as_contemporaneous_and_positive_as_forward() -> None:
    weekly = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-03", periods=5, freq="W-WED"),
            "component": "sp500",
            "series_id": "SP500",
            "value": [100.0, 110.0, 121.0, 133.1, 146.41],
            "unit": "Index",
        }
    )

    result = calculate_market_forward_returns(weekly, horizons_weeks=(0, 2))
    current = result.loc[result["horizon_weeks"] == 0].reset_index(drop=True)
    forward = result.loc[result["horizon_weeks"] == 2].reset_index(drop=True)

    assert np.isclose(current.loc[1, "market_return"], 0.1)
    assert current.loc[1, "return_start_date"] == pd.Timestamp("2024-01-03")
    assert np.isclose(forward.loc[0, "market_return"], 0.21)
    assert forward.loc[0, "return_end_date"] == pd.Timestamp("2024-01-17")
    assert forward["market_return"].tail(2).isna().all()


def test_comparison_preserves_liquidity_signal_at_anchor_date() -> None:
    dates = pd.date_range("2024-01-03", periods=3, freq="W-WED")
    ogli = pd.DataFrame(
        {
            "date": dates,
            "model_id": "model_a",
            "model_name": "Model A",
            "ogli": [40.0, 50.0, 60.0],
            "momentum_score": [-0.2, 0.0, 0.2],
            "growth_3m_annualized": [0.01, 0.02, 0.03],
            "growth_12m_yoy": [0.02, 0.03, 0.04],
        }
    )
    returns = pd.DataFrame(
        {
            "date": dates,
            "market_id": "sp500",
            "series_id": "SP500",
            "horizon_weeks": 4,
            "return_type": "forward",
            "market_return": [0.03, 0.04, 0.05],
            "return_start_date": dates,
            "return_end_date": dates + pd.Timedelta(weeks=4),
        }
    )

    result = build_liquidity_market_comparison(ogli, returns)

    assert result["liquidity_signal"].tolist() == [-0.2, 0.0, 0.2]
    assert result["liquidity_signal_name"].unique().tolist() == ["momentum_score"]
