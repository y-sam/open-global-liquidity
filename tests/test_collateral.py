from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from open_global_liquidity.models.collateral import (
    CollateralModelError,
    calculate_collateral_conditions,
    load_collateral_config,
)


def _config():
    return load_collateral_config(Path("config/collateral.yaml"))


def _source(periods: int = 72) -> pd.DataFrame:
    dates = pd.date_range("2018-04-30", periods=periods, freq="ME")
    rows = []
    for index, month_end in enumerate(dates):
        rows.extend(
            [
                (month_end, "marketable_treasury_debt_public", 15_000_000 + index * 100_000),
                (
                    month_end - pd.Timedelta(days=3),
                    "fed_treasury_holdings",
                    2_000_000 + index * 5_000,
                ),
            ]
        )
        business_days = pd.bdate_range(month_end - pd.offsets.MonthBegin(), month_end)
        for day_index, day in enumerate(business_days):
            rows.extend(
                [
                    (day, "secured_overnight_financing_rate", 2.0 + 0.01 * (index % 7)),
                    (day, "effective_federal_funds_rate", 1.95),
                    (
                        day,
                        "treasury_yield_10y_collateral",
                        3.0 + 0.02 * np.sin(index + day_index),
                    ),
                ]
            )
    return pd.DataFrame(rows, columns=["date", "component", "value"]).assign(
        provider="test",
        series_id=lambda frame: frame["component"],
        retrieved_at=pd.Timestamp("2026-01-01", tz="UTC"),
    )


def test_config_separates_assumptions_from_calibration() -> None:
    config = _config()

    assert config.classification == "model_assumption"
    assert config.normalization_mode == "expanding"
    assert sum(item.weight for item in config.components) == pytest.approx(1.0)
    assert {item.direction for item in config.components} == {-1, 1}


def test_collateral_score_is_bounded_and_non_look_ahead() -> None:
    source = _source()
    result = calculate_collateral_conditions(source, _config())

    valid = result.dropna(subset=["collateral_conditions_index"])
    assert not valid.empty
    assert valid["collateral_conditions_index"].between(0, 100).all()
    assert (result["private_collateral_proxy_millions"] > 0).all()
    assert set(result["normalization_mode"]) == {"expanding"}

    changed = source.copy()
    last_date = changed["date"].max()
    changed.loc[
        (changed["date"] == last_date)
        & (changed["component"] == "marketable_treasury_debt_public"),
        "value",
    ] *= 3
    revised = calculate_collateral_conditions(changed, _config())
    first_valid_date = valid.iloc[0]["date"]
    original_value = result.loc[
        result["date"] == first_valid_date, "collateral_conditions_index"
    ].iloc[0]
    revised_value = revised.loc[
        revised["date"] == first_valid_date, "collateral_conditions_index"
    ].iloc[0]
    assert revised_value == pytest.approx(original_value)


def test_collateral_model_rejects_missing_component() -> None:
    source = _source().loc[lambda frame: frame["component"] != "fed_treasury_holdings"]

    with pytest.raises(CollateralModelError, match="lacks components"):
        calculate_collateral_conditions(source, _config())


def test_collateral_model_omits_missing_daily_observations_without_interpolation() -> None:
    source = _source()
    missing_row = source.loc[source["component"] == "treasury_yield_10y_collateral"].index[30]
    source.loc[missing_row, "value"] = float("nan")

    result = calculate_collateral_conditions(source, _config())

    assert result["treasury_volatility_bps"].notna().any()
    assert result["collateral_conditions_index"].notna().any()
