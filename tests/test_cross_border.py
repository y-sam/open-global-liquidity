from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.models.cross_border import (
    CrossBorderModelError,
    calculate_cross_border_credit,
    load_cross_border_config,
)


def _source(periods: int = 24) -> pd.DataFrame:
    dates = pd.date_range("2015-03-31", periods=periods, freq="QE")
    return pd.DataFrame(
        {
            "date": dates,
            "component": "usd_credit_nonbanks_outside_us",
            "value": [10_000_000 * (1.01**index) for index in range(periods)],
            "provider": "BIS",
            "series_id": "BIS,WS_GLI,1.0/Q.USD.3P.N.A.I.B.USD",
            "retrieved_at": pd.Timestamp("2026-01-01", tz="UTC"),
        }
    )


def test_cross_border_index_is_non_look_ahead_and_source_timed() -> None:
    config = load_cross_border_config(Path("config/cross_border.yaml"))
    source = _source()

    result = calculate_cross_border_credit(source, config)

    assert result["offshore_dollar_credit_index"].dropna().between(0, 100).all()
    assert result["signal_available_date"].equals(result["date"] + pd.offsets.MonthEnd(4))
    first_valid = result["offshore_dollar_credit_index"].first_valid_index()
    changed = source.copy()
    changed.loc[changed.index[-1], "value"] *= 2
    revised = calculate_cross_border_credit(changed, config)
    assert revised.loc[first_valid, "offshore_dollar_credit_index"] == pytest.approx(
        result.loc[first_valid, "offshore_dollar_credit_index"]
    )


def test_cross_border_rejects_duplicate_periods() -> None:
    source = pd.concat([_source(), _source().iloc[[0]]], ignore_index=True)

    with pytest.raises(CrossBorderModelError, match="unique positive"):
        calculate_cross_border_credit(
            source, load_cross_border_config(Path("config/cross_border.yaml"))
        )
