import pandas as pd
import pytest

from open_global_liquidity.analysis.point_in_time_markets import (
    build_point_in_time_market_pairs,
    summarize_point_in_time_market_pairs,
)


def _signals(periods: int = 18) -> pd.DataFrame:
    dates = pd.date_range("2022-01-31", periods=periods, freq="ME")
    return pd.DataFrame(
        {
            "information_date": dates,
            "signal_observation_date": dates - pd.Timedelta(days=5),
            "model_id": ["model_b"] * periods,
            "model_name": ["Model B"] * periods,
            "vintage_ogli": range(40, 40 + periods),
            "vintage_momentum_score": [index / 10 for index in range(periods)],
            "vintage_regime": ["Neutral"] * periods,
        }
    )


def _daily_market() -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", "2024-12-31", freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "component": ["bitcoin"] * len(dates),
            "series_id": ["btc.PriceUSD"] * len(dates),
            "provider": ["Coin Metrics"] * len(dates),
            "value": [100.0 + index for index in range(len(dates))],
            "unit": ["U.S. Dollars per Bitcoin"] * len(dates),
            "frequency": ["Daily"] * len(dates),
        }
    )


def test_pairs_apply_publication_delay_before_market_return() -> None:
    pairs = build_point_in_time_market_pairs(
        _signals(3),
        _daily_market(),
        publication_lag_weeks=[0, 2],
        forward_horizons_months=[1],
    )

    delayed = pairs.loc[pairs["publication_lag_weeks"] == 2].iloc[0]
    assert delayed["signal_available_date"] == delayed["information_date"] + pd.Timedelta(weeks=2)
    assert delayed["start_observation_date"] <= delayed["start_target_date"]
    assert delayed["end_observation_date"] <= delayed["end_target_date"]
    assert delayed["market_return"] == pytest.approx(
        delayed["end_value"] / delayed["start_value"] - 1
    )


def test_pairs_mark_mechanically_non_overlapping_monthly_samples() -> None:
    pairs = build_point_in_time_market_pairs(
        _signals(12),
        _daily_market(),
        publication_lag_weeks=[0],
        forward_horizons_months=[3],
    )

    assert pairs["is_non_overlapping"].sum() == 4


def test_summary_separates_overlapping_and_non_overlapping_samples() -> None:
    pairs = build_point_in_time_market_pairs(
        _signals(),
        _daily_market(),
        publication_lag_weeks=[0],
        forward_horizons_months=[3],
    )
    summary = summarize_point_in_time_market_pairs(
        pairs, min_periods=3, non_overlapping_min_periods=3
    ).set_index("sample_policy")

    assert summary.loc["overlapping", "observations"] == 18
    assert summary.loc["non_overlapping", "observations"] == 6
    assert summary.loc["overlapping", "positive_share"] == 1.0
    assert pd.notna(summary.loc["non_overlapping", "correlation"])
