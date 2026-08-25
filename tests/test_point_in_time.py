import json
from datetime import UTC, date
from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.config import load_model_config
from open_global_liquidity.data.fred import VINTAGE_COLUMNS
from open_global_liquidity.point_in_time import (
    PointInTimeError,
    build_month_end_grid,
    calculate_point_in_time_ogli,
    compare_point_in_time_to_current,
)
from open_global_liquidity.point_in_time_pipeline import _publish_dashboard_snapshot


def test_build_month_end_grid_uses_only_completed_months() -> None:
    assert build_month_end_grid("2024-01-15", "2024-03-20") == (
        date(2024, 1, 31),
        date(2024, 2, 29),
    )
    assert build_month_end_grid("2024-01-31", "2024-03-31")[-1] == date(2024, 3, 31)


def test_calculate_point_in_time_ogli_seals_each_vintage() -> None:
    config = load_model_config(Path("config/model.yaml"))
    dates = pd.date_range("2020-01-01", periods=160, freq="W-WED")
    definitions = {
        "WALCL": ("fed_assets", "Millions of U.S. Dollars", 8_000_000.0, 2_000.0),
        "WDTGAL": (
            "treasury_general_account",
            "Millions of U.S. Dollars",
            500_000.0,
            100.0,
        ),
        "RRPONTSYD": (
            "overnight_reverse_repo",
            "Billions of U.S. Dollars",
            1_000.0,
            -1.0,
        ),
        "WRBWFRBL": (
            "reserve_balances",
            "Millions of U.S. Dollars",
            3_000_000.0,
            1_200.0,
        ),
    }
    frames = []
    for vintage_date in (pd.Timestamp("2023-01-31"), pd.Timestamp("2023-02-28")):
        visible_dates = dates[dates <= vintage_date]
        for series_id, (component, unit, initial, step) in definitions.items():
            frames.append(
                pd.DataFrame(
                    {
                        "observation_date": visible_dates,
                        "vintage_date": vintage_date,
                        "country": "US",
                        "provider": "ALFRED",
                        "series_id": series_id,
                        "component": component,
                        "value": [initial + step * index for index in range(len(visible_dates))],
                        "unit": unit,
                        "frequency": (
                            "Daily" if series_id == "RRPONTSYD" else "Weekly, As of Wednesday"
                        ),
                        "realtime_start": pd.NA,
                        "realtime_end": pd.NA,
                        "retrieved_at": pd.Timestamp("2024-01-01", tz=UTC),
                    }
                )
            )
    vintage_inputs = pd.concat(frames, ignore_index=True)[VINTAGE_COLUMNS]

    result = calculate_point_in_time_ogli(vintage_inputs, config)

    assert len(result) == 6
    assert result.groupby("information_date")["model_id"].nunique().eq(3).all()
    assert (result["signal_observation_date"] <= result["information_date"]).all()
    assert result["vintage_ogli"].between(0, 100).all()


def test_compare_point_in_time_to_current_uses_same_signal_date() -> None:
    point_in_time = pd.DataFrame(
        {
            "information_date": pd.to_datetime(["2024-01-31"]),
            "signal_observation_date": pd.to_datetime(["2024-01-24"]),
            "model_id": ["model_a"],
            "vintage_ogli": [40.0],
            "vintage_momentum_score": [-0.2],
        }
    )
    current = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-24"]),
            "model_id": ["model_a"],
            "ogli": [44.0],
            "momentum_score": [-0.1],
            "regime": ["Below normal"],
        }
    )

    result = compare_point_in_time_to_current(point_in_time, current)

    assert result.loc[0, "ogli_revision"] == 4.0
    assert result.loc[0, "momentum_revision"] == pytest.approx(0.1)
    assert result.loc[0, "comparison_policy"] == "same_observation_date"


def test_compare_point_in_time_rejects_missing_exact_date() -> None:
    point_in_time = pd.DataFrame(
        {
            "information_date": pd.to_datetime(["2024-01-31"]),
            "signal_observation_date": pd.to_datetime(["2024-01-24"]),
            "model_id": ["model_a"],
            "vintage_ogli": [40.0],
            "vintage_momentum_score": [-0.2],
        }
    )
    current = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-31"]),
            "model_id": ["model_a"],
            "ogli": [44.0],
            "momentum_score": [-0.1],
            "regime": ["Below normal"],
        }
    )

    with pytest.raises(PointInTimeError, match="lacks an exact comparison"):
        compare_point_in_time_to_current(point_in_time, current)


def test_publish_dashboard_snapshot_refreshes_whole_manifest(tmp_path: Path) -> None:
    reference = tmp_path / "data" / "reference"
    reference.mkdir(parents=True)
    pd.DataFrame({"date": pd.to_datetime(["2024-01-03"]), "value": [1.0]}).to_parquet(
        reference / "existing_snapshot.parquet", index=False
    )
    comparison = pd.DataFrame(
        {
            "information_date": pd.to_datetime(["2024-01-31"]),
            "signal_observation_date": pd.to_datetime(["2024-01-24"]),
            "model_id": ["model_a"],
            "vintage_ogli": [40.0],
            "current_ogli": [44.0],
        }
    )

    path = _publish_dashboard_snapshot(comparison, project_root=tmp_path)
    manifest = json.loads(
        (reference / "dashboard_snapshot_manifest.json").read_text(encoding="utf-8")
    )

    assert path.name == "us_point_in_time_comparison_snapshot.parquet"
    assert manifest["snapshot_count"] == 2
    assert path.name in manifest["files"]
