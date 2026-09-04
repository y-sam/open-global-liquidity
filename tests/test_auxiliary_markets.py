from pathlib import Path

import pandas as pd

from open_global_liquidity.analysis.auxiliary_markets import (
    build_auxiliary_bitcoin_pairs,
    load_auxiliary_validation_config,
    summarize_auxiliary_bitcoin_pairs,
)


def _signals() -> pd.DataFrame:
    dates = pd.date_range("2015-03-31", periods=36, freq="QE")
    return pd.DataFrame(
        {
            "date": dates,
            "signal_available_date": dates + pd.offsets.MonthEnd(4),
            "momentum_score": [(index - 18) / 10 for index in range(len(dates))],
            "offshore_dollar_credit_index": [20 + index for index in range(len(dates))],
            "regime": ["Neutral"] * len(dates),
        }
    )


def _bitcoin() -> pd.DataFrame:
    dates = pd.date_range("2015-01-01", "2025-12-31", freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "component": "bitcoin",
            "series_id": "btc.PriceUSD",
            "provider": "COINMETRICS",
            "value": 1_000 + pd.Series(range(len(dates)), dtype=float),
        }
    )


def test_auxiliary_validation_is_frozen_and_builds_source_timed_pairs() -> None:
    config = load_auxiliary_validation_config(Path("config/auxiliary_validation.yaml"))
    definition = next(item for item in config.signals if item.model_id == "offshore_dollar_credit")

    pairs = build_auxiliary_bitcoin_pairs(_signals(), _bitcoin(), definition, config)

    assert set(pairs["additional_availability_lag_months"]) == {0, 1, 2}
    assert set(pairs["horizon_months"]) == {1, 3, 6, 12}
    assert pairs.loc[pairs["specification_role"] == "primary", "horizon_months"].eq(6).all()
    assert (
        pairs.loc[pairs["specification_role"] == "primary", "additional_availability_lag_months"]
        .eq(0)
        .all()
    )
    assert (pairs["signal_available_date"] >= pairs["source_available_date"]).all()


def test_auxiliary_pairing_accepts_parquet_microsecond_timestamps(tmp_path: Path) -> None:
    config = load_auxiliary_validation_config(Path("config/auxiliary_validation.yaml"))
    definition = next(item for item in config.signals if item.model_id == "offshore_dollar_credit")
    signal_path = tmp_path / "signals.parquet"
    _signals().to_parquet(signal_path, index=False)
    signals = pd.read_parquet(signal_path)

    pairs = build_auxiliary_bitcoin_pairs(signals, _bitcoin(), definition, config)

    assert not pairs.empty


def test_non_overlapping_quarterly_windows_are_date_based() -> None:
    config = load_auxiliary_validation_config(Path("config/auxiliary_validation.yaml"))
    definition = next(item for item in config.signals if item.model_id == "offshore_dollar_credit")
    pairs = build_auxiliary_bitcoin_pairs(_signals(), _bitcoin(), definition, config)
    six_month = pairs.loc[
        (pairs["additional_availability_lag_months"] == 0) & (pairs["horizon_months"] == 6)
    ]
    selected = six_month.loc[six_month["is_non_overlapping"]].sort_values("signal_available_date")

    assert len(selected) >= 8
    assert (
        selected["signal_available_date"].iloc[1:].reset_index(drop=True)
        >= selected["end_target_date"].iloc[:-1].reset_index(drop=True)
    ).all()


def test_auxiliary_summary_reports_primary_uncertainty() -> None:
    config = load_auxiliary_validation_config(Path("config/auxiliary_validation.yaml"))
    definition = next(item for item in config.signals if item.model_id == "offshore_dollar_credit")
    pairs = build_auxiliary_bitcoin_pairs(_signals(), _bitcoin(), definition, config)

    summary = summarize_auxiliary_bitcoin_pairs(pairs, config)
    primary = summary.loc[
        (summary["specification_role"] == "primary")
        & (summary["sample_policy"] == config.primary_sample_policy)
    ].iloc[0]

    assert primary["observations"] >= config.non_overlapping_min_periods
    assert pd.notna(primary["correlation"])
    assert primary["bootstrap_valid_resamples"] == config.bootstrap_resamples
    assert primary["bootstrap_ci_lower"] <= primary["bootstrap_ci_upper"]
