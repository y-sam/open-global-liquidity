import pandas as pd

from open_global_liquidity.analysis.collateral_markets import (
    build_collateral_bitcoin_pairs,
    summarize_collateral_bitcoin_pairs,
)


def _collateral(periods: int = 48) -> pd.DataFrame:
    dates = pd.date_range("2020-01-31", periods=periods, freq="ME")
    result = pd.DataFrame(
        {
            "date": dates,
            "collateral_conditions_score": [index / 20 - 1 for index in range(periods)],
            "collateral_conditions_index": [30 + index for index in range(periods)],
            "collateral_regime": ["Neutral"] * periods,
            "model_name": ["Open Collateral Conditions Score"] * periods,
        }
    )
    result["signal_available_date"] = result["date"] + pd.offsets.BDay(4)
    return result


def _bitcoin() -> pd.DataFrame:
    dates = pd.date_range("2019-12-01", "2025-12-31", freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "component": "bitcoin",
            "series_id": "btc.PriceUSD",
            "provider": "Coin Metrics",
            "value": [10_000 * (1.0005**index) for index in range(len(dates))],
        }
    )


def test_collateral_bitcoin_validation_keeps_timing_and_uncertainty_explicit() -> None:
    pairs = build_collateral_bitcoin_pairs(
        _collateral(),
        _bitcoin(),
        availability_lag_months=(0, 1),
        forward_horizons_months=(1, 3),
    )
    summary = summarize_collateral_bitcoin_pairs(
        pairs,
        overlapping_min_periods=12,
        non_overlapping_min_periods=8,
        confidence_level=0.95,
        bootstrap_resamples=100,
        bootstrap_block_length=4,
        bootstrap_seed=42,
    )

    delayed = pairs.loc[pairs["availability_lag_months"] == 1].iloc[0]
    assert delayed["source_available_date"] == delayed["signal_date"] + pd.offsets.BDay(4)
    assert delayed["signal_available_date"] == delayed["source_available_date"] + pd.DateOffset(
        months=1
    )
    assert set(summary["sample_policy"]) == {"overlapping", "non_overlapping"}
    available = summary.dropna(subset=["correlation"])
    assert available["bootstrap_valid_resamples"].eq(100).all()
    assert (available["bootstrap_ci_lower"] <= available["bootstrap_ci_upper"]).all()
