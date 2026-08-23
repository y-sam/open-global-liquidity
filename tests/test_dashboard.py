import importlib.util
from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.dashboard import (
    DashboardDataError,
    latest_model_readings,
    latest_readings,
    load_dashboard_data,
    load_liquidity_model_data,
    resolve_dashboard_data_path,
)


def _processed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03", "2024-01-10", "2024-01-10"]),
            "country": ["US"] * 3,
            "provider": ["FRED"] * 3,
            "series_id": ["WALCL", "WALCL", "RRPONTSYD"],
            "component": ["fed_assets", "fed_assets", "overnight_reverse_repo"],
            "value": [6_700_000.0, 6_800_000.0, 500.0],
            "unit": [
                "Millions of U.S. Dollars",
                "Millions of U.S. Dollars",
                "Billions of U.S. Dollars",
            ],
            "frequency": ["Weekly, As of Wednesday"] * 2 + ["Daily"],
            "retrieved_at": [pd.Timestamp("2024-01-11", tz=UTC)] * 3,
        }
    )


def test_load_dashboard_data_converts_units_to_billions(tmp_path: Path) -> None:
    path = tmp_path / "processed.parquet"
    _processed_frame().to_parquet(path, index=False)

    result = load_dashboard_data(path)

    assert result.loc[result["series_id"] == "WALCL", "value_usd_billions"].tolist() == [
        6_700.0,
        6_800.0,
    ]
    assert result.loc[result["series_id"] == "RRPONTSYD", "value_usd_billions"].item() == 500.0


def test_latest_readings_calculates_one_observation_change(tmp_path: Path) -> None:
    path = tmp_path / "processed.parquet"
    _processed_frame().to_parquet(path, index=False)

    result = latest_readings(load_dashboard_data(path)).set_index("component")

    assert result.loc["fed_assets", "value_usd_billions"] == 6_800.0
    assert result.loc["fed_assets", "change_usd_billions"] == 100.0
    assert pd.isna(result.loc["overnight_reverse_repo", "change_usd_billions"])


def test_dashboard_rejects_unsupported_units(tmp_path: Path) -> None:
    path = tmp_path / "processed.parquet"
    frame = _processed_frame()
    frame["unit"] = "Percent"
    frame.to_parquet(path, index=False)

    with pytest.raises(DashboardDataError, match="cannot convert"):
        load_dashboard_data(path)


def test_dashboard_prefers_processed_data_over_snapshot(tmp_path: Path) -> None:
    processed = tmp_path / "processed.parquet"
    snapshot = tmp_path / "snapshot.parquet"
    processed.touch()
    snapshot.touch()

    path, origin = resolve_dashboard_data_path(processed, snapshot)

    assert path == processed
    assert origin == "Local processed data"


def test_dashboard_falls_back_to_public_snapshot(tmp_path: Path) -> None:
    processed = tmp_path / "processed.parquet"
    snapshot = tmp_path / "snapshot.parquet"
    snapshot.touch()

    path, origin = resolve_dashboard_data_path(processed, snapshot)

    assert path == snapshot
    assert origin == "Bundled public snapshot"


def test_dashboard_fails_clearly_without_any_data(tmp_path: Path) -> None:
    with pytest.raises(DashboardDataError, match="No dashboard data"):
        resolve_dashboard_data_path(tmp_path / "processed.parquet", tmp_path / "snapshot.parquet")


def test_loads_liquidity_models_and_calculates_latest_change(tmp_path: Path) -> None:
    path = tmp_path / "models.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03", "2024-01-10"]),
            "model_id": ["model_a", "model_a"],
            "model_name": ["Model A", "Model A"],
            "value": [8_000_000.0, 8_100_000.0],
            "unit": ["Millions of U.S. Dollars"] * 2,
            "frequency": ["Weekly, As of Wednesday"] * 2,
            "classification": ["model_assumption"] * 2,
            "formula": ["fed_assets"] * 2,
            "description": ["Test"] * 2,
            "is_complete": [True, True],
        }
    ).to_parquet(path, index=False)

    result = load_liquidity_model_data(path)
    latest = latest_model_readings(result).iloc[0]

    assert result["value_usd_billions"].tolist() == [8_000.0, 8_100.0]
    assert latest["value_usd_billions"] == 8_100.0
    assert latest["change_usd_billions"] == 100.0


def test_loads_calculated_ogli_and_selects_latest_available_reading(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_under_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    path = tmp_path / "ogli.parquet"
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03", "2024-01-10"]),
            "model_id": ["model_a", "model_a"],
            "model_name": ["Model A", "Model A"],
            "value": [8_000_000.0, 8_100_000.0],
            "change_1m": [pd.NA, 100_000.0],
            "change_3m": [pd.NA, 200_000.0],
            "change_6m": [pd.NA, 300_000.0],
            "change_12m": [pd.NA, 400_000.0],
            "growth_3m_annualized": [pd.NA, 0.12],
            "growth_12m_yoy": [pd.NA, 0.08],
            "z_growth_3m_annualized": [pd.NA, 0.5],
            "z_growth_12m_yoy": [pd.NA, 0.25],
            "momentum_score": [pd.NA, 0.4],
            "ogli": [pd.NA, 65.54],
            "regime": [None, "Above normal"],
            "zscore_mode": ["expanding", "expanding"],
            "zscore_min_periods": [104, 104],
            "ogli_classification": ["statistical_transformation"] * 2,
            "weight_classification": ["model_assumption"] * 2,
        }
    )
    frame.to_parquet(path, index=False)

    loaded = support.load_ogli_data(path)
    latest = support.latest_ogli_readings(loaded).iloc[0]

    assert latest["ogli"] == 65.54
    assert latest["regime"] == "Above normal"
    assert latest["date"] == pd.Timestamp("2024-01-10")
