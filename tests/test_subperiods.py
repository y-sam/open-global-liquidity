from datetime import date

import numpy as np
import pandas as pd

from open_global_liquidity.analysis.subperiods import calculate_subperiod_correlations
from open_global_liquidity.config import MarketResearchSubperiod


def test_subperiod_correlations_keep_predeclared_periods_and_sample_policies() -> None:
    dates = pd.date_range("2019-11-06", periods=16, freq="W-WED")
    values = np.arange(16, dtype=float)
    comparisons = pd.DataFrame(
        {
            "date": dates,
            "signal_observation_date": dates,
            "model_id": "model_b",
            "model_name": "Model B",
            "market_id": "bitcoin",
            "series_id": "btc.PriceUSD",
            "horizon_weeks": 4,
            "return_type": "forward",
            "analysis_mode": "available_information",
            "liquidity_signal_name": "momentum_score",
            "liquidity_signal": values,
            "market_return": values * 0.1,
            "return_start_date": dates,
            "return_end_date": dates + pd.Timedelta(weeks=4),
        }
    )
    periods = (
        MarketResearchSubperiod(
            period_id="before", label="Before", start=date(2019, 1, 1), end=date(2019, 12, 31)
        ),
        MarketResearchSubperiod(period_id="after", label="After", start=date(2020, 1, 1), end=None),
    )

    result = calculate_subperiod_correlations(
        comparisons,
        periods,
        overlapping_min_periods=2,
        non_overlapping_min_periods=2,
        confidence_level=0.95,
    )

    assert set(result["period_id"]) == {"before", "after"}
    assert set(result["sample_policy"]) == {"overlapping", "non_overlapping"}
    assert set(result["period_classification"]) == {"model_assumption"}
    assert np.allclose(result["correlation"].dropna(), 1.0)
