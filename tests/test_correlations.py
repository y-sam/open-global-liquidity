import numpy as np
import pandas as pd

from open_global_liquidity.analysis.correlations import (
    add_rolling_correlations,
    calculate_lagged_correlations,
)


def _comparisons() -> pd.DataFrame:
    values = np.arange(8, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-03", periods=8, freq="W-WED"),
            "model_id": "model_a",
            "model_name": "Model A",
            "market_id": "sp500",
            "series_id": "SP500",
            "horizon_weeks": 4,
            "return_type": "forward",
            "liquidity_signal_name": "momentum_score",
            "liquidity_signal": values,
            "market_return": values * 0.1,
        }
    )


def test_lagged_correlation_reports_observation_count_and_perfect_relationship() -> None:
    result = calculate_lagged_correlations(_comparisons(), min_periods=5).iloc[0]

    assert np.isclose(result["correlation"], 1.0)
    assert result["observations"] == 8


def test_rolling_correlation_respects_minimum_history() -> None:
    result = add_rolling_correlations(_comparisons(), window_weeks=4, min_periods=3)

    assert result["rolling_correlation"].iloc[:2].isna().all()
    np.testing.assert_allclose(result["rolling_correlation"].iloc[2:], 1.0)
