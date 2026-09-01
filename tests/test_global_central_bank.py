from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.models.global_central_bank import (
    GlobalAggregationError,
    calculate_global_central_bank_assets,
    calculate_global_central_bank_index,
    load_global_aggregation_config,
)


def _config():
    return load_global_aggregation_config(Path("config/global_aggregation.yaml"))


def test_load_global_aggregation_config_is_explicit() -> None:
    config = _config()

    assert config.classification == "model_assumption"
    assert config.canonical_frequency == "quarter_end"
    assert config.missing_policy == "balanced_panel_only"
    assert len(config.components) == 5
    assert config.components[-1].fx_component == "yuan_per_usd"
    assert config.index.normalization == "expanding"
    assert config.index.min_periods == 20
    assert sum(config.index.momentum_weights.values()) == pytest.approx(1.0)


def test_calculate_global_assets_converts_direct_and_inverse_quotes() -> None:
    config = _config()
    dates = pd.to_datetime(["2013-09-30", "2013-12-31"])
    values = {
        "fed_assets": ("Millions of U.S. Dollars", [4_000_000.0, 4_100_000.0]),
        "eurosystem_total_assets": ("Millions of Euro", [3_000_000.0, 3_100_000.0]),
        "boj_total_assets": ("100 Million Yen", [1_000.0, 1_100.0]),
        "boe_total_assets": ("Millions of Sterling", [500_000.0, 510_000.0]),
        "china_central_bank_total_assets": (
            "Billions of Chinese Yuan",
            [30_000.0, 31_000.0],
        ),
    }
    source_rows = []
    for component, (unit, component_values) in values.items():
        for observation_date, value in zip(dates, component_values, strict=True):
            source_rows.append(
                {"date": observation_date, "component": component, "value": value, "unit": unit}
            )
    fx_values = {
        "usd_per_euro": [1.3, 1.4],
        "yen_per_usd": [100.0, 110.0],
        "usd_per_sterling": [1.5, 1.6],
        "yuan_per_usd": [6.0, 6.2],
    }
    fx_rows = []
    for component, component_values in fx_values.items():
        for observation_date, value in zip(dates, component_values, strict=True):
            fx_rows.append(
                {
                    "date": observation_date,
                    "component": component,
                    "value": (
                        pd.NA
                        if component == "usd_per_euro"
                        and observation_date == pd.Timestamp("2013-12-31")
                        else value
                    ),
                    "unit": "FX",
                }
            )
    fx_rows.append(
        {
            "date": pd.Timestamp("2013-12-30"),
            "component": "usd_per_euro",
            "value": 1.4,
            "unit": "FX",
        }
    )

    detail, aggregate = calculate_global_central_bank_assets(
        pd.DataFrame(source_rows), pd.DataFrame(fx_rows), config
    )

    first = detail.loc[detail["date"] == dates[0]].set_index("component")
    assert first.loc["eurosystem_total_assets", "value_usd_millions"] == 3_900_000.0
    assert first.loc["boj_total_assets", "value_usd_millions"] == 1_000.0
    assert first.loc["china_central_bank_total_assets", "value_usd_millions"] == 5_000_000.0
    assert aggregate.iloc[0]["total_usd_millions"] == 13_651_000.0
    assert aggregate["component_count"].tolist() == [5, 5]


def test_global_index_uses_expanding_history_and_is_bounded() -> None:
    dates = pd.date_range("2010-03-31", periods=32, freq="QE")
    values = pd.Series(
        [10_000_000 * (1.01**period) * (1 + 0.01 * ((period % 5) - 2)) for period in range(32)]
    )
    aggregate = pd.DataFrame(
        {
            "date": dates,
            "total_usd_millions": values,
            "change_1q": values.pct_change(),
            "growth_yoy": values.pct_change(4),
        }
    )

    result = calculate_global_central_bank_index(aggregate, _config())

    valid = result.dropna(subset=["global_cb_index"])
    assert not valid.empty
    assert valid["global_cb_index"].between(0, 100).all()
    assert set(valid["global_cb_zscore_mode"]) == {"expanding"}
    assert set(valid["global_cb_index_classification"]) == {"statistical_transformation"}
    first_valid = valid.index[0]
    changed_future = aggregate.copy()
    changed_future.loc[changed_future.index[-1], "total_usd_millions"] *= 10
    changed_future["change_1q"] = changed_future["total_usd_millions"].pct_change()
    changed_future["growth_yoy"] = changed_future["total_usd_millions"].pct_change(4)
    revised = calculate_global_central_bank_index(changed_future, _config())
    assert revised.loc[first_valid, "global_cb_index"] == pytest.approx(
        result.loc[first_valid, "global_cb_index"]
    )


def test_calculate_global_assets_rejects_missing_component() -> None:
    source = pd.DataFrame(
        {
            "date": [pd.Timestamp("2013-09-30")],
            "component": ["fed_assets"],
            "value": [1.0],
            "unit": ["Millions of U.S. Dollars"],
        }
    )
    fx = pd.DataFrame(columns=["date", "component", "value", "unit"])

    with pytest.raises(GlobalAggregationError, match="missing configured components"):
        calculate_global_central_bank_assets(source, fx, _config())
