from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.dashboard import (
    DashboardDataError,
    latest_readings,
    load_dashboard_data,
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
