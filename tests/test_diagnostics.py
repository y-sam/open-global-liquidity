import numpy as np
import pandas as pd

from open_global_liquidity.analysis.diagnostics import (
    calculate_regime_return_statistics,
    select_non_overlapping_returns,
)


def _comparisons() -> pd.DataFrame:
    dates = pd.date_range("2024-01-03", periods=8, freq="W-WED")
    return pd.DataFrame(
        {
            "date": dates,
            "model_id": "model_b",
            "model_name": "Model B",
            "market_id": "bitcoin",
            "series_id": "btc.PriceUSD",
            "horizon_weeks": 4,
            "return_type": "forward",
            "analysis_mode": "available_information",
            "regime": ["Expansion"] * 8,
            "market_return": [0.10, 0.20, -0.10, 0.05, 0.30, -0.20, 0.15, 0.25],
            "return_start_date": dates,
            "return_end_date": dates + pd.Timedelta(weeks=4),
        }
    )


def test_non_overlapping_selector_uses_adjacent_disjoint_windows() -> None:
    result = select_non_overlapping_returns(_comparisons())

    assert result["date"].tolist() == [pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-31")]


def test_regime_statistics_report_median_positive_share_and_interval() -> None:
    result = calculate_regime_return_statistics(
        _comparisons(), sample_policy="overlapping", confidence_level=0.95
    ).iloc[0]

    assert result["observations"] == 8
    assert np.isclose(result["median_return"], 0.125)
    assert np.isclose(result["positive_share"], 0.75)
    assert result["mean_ci_lower"] < result["mean_return"] < result["mean_ci_upper"]
