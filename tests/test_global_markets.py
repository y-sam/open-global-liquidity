import pandas as pd
import pytest

from open_global_liquidity.analysis.global_markets import (
    GlobalMarketAnalysisError,
    build_global_bitcoin_pairs,
    summarize_global_bitcoin_pairs,
)


def _global_index(periods: int = 36) -> pd.DataFrame:
    dates = pd.date_range("2020-01-31", periods=periods, freq="ME")
    return pd.DataFrame(
        {
            "date": dates,
            "global_cb_index": [40 + period / 2 for period in range(periods)],
            "global_cb_momentum_score": [period / 20 - 0.5 for period in range(periods)],
            "global_cb_regime": ["Neutral"] * periods,
            "global_cb_index_name": ["Global Model G"] * periods,
        }
    )


def _bitcoin() -> pd.DataFrame:
    dates = pd.date_range("2019-12-01", "2024-12-31", freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "component": "bitcoin",
            "series_id": "btc.PriceUSD",
            "provider": "Coin Metrics",
            "value": [10_000 * (1.0005**period) for period in range(len(dates))],
        }
    )


def test_build_global_bitcoin_pairs_applies_lag_and_horizon() -> None:
    pairs = build_global_bitcoin_pairs(
        _global_index(),
        _bitcoin(),
        availability_lag_months=(0, 2),
        forward_horizons_months=(1, 3),
    )

    row = pairs.loc[(pairs["availability_lag_months"] == 2) & (pairs["horizon_months"] == 3)].iloc[
        0
    ]
    assert row["signal_available_date"] == row["signal_date"] + pd.DateOffset(months=2)
    assert row["end_observation_date"] <= row["signal_available_date"] + pd.DateOffset(months=3)
    assert pairs["market_return"].gt(0).all()
    assert set(pairs["timing_classification"]) == {"model_assumption"}


def test_summarize_global_bitcoin_pairs_retains_both_sample_policies() -> None:
    pairs = build_global_bitcoin_pairs(
        _global_index(),
        _bitcoin(),
        availability_lag_months=(1,),
        forward_horizons_months=(1, 6),
    )

    summary = summarize_global_bitcoin_pairs(
        pairs,
        overlapping_min_periods=12,
        non_overlapping_min_periods=4,
    )

    assert set(summary["sample_policy"]) == {"overlapping", "non_overlapping"}
    assert summary.loc[summary["sample_policy"] == "overlapping", "correlation"].notna().all()
    assert summary["positive_share"].eq(1).all()


def test_global_bitcoin_pairs_require_bitcoin() -> None:
    markets = _bitcoin().assign(component="gold")

    with pytest.raises(GlobalMarketAnalysisError, match="positive Bitcoin levels"):
        build_global_bitcoin_pairs(
            _global_index(),
            markets,
            availability_lag_months=(0,),
            forward_horizons_months=(1,),
        )
