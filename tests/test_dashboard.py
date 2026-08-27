import importlib.util
import json
from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.dashboard import (
    DashboardDataError,
    latest_boj_readings,
    latest_ecb_readings,
    latest_model_readings,
    latest_readings,
    load_boj_data,
    load_dashboard_data,
    load_ecb_data,
    load_liquidity_model_data,
    resolve_dashboard_data_path,
)


def test_load_boj_data_and_latest_changes(tmp_path: Path) -> None:
    path = tmp_path / "boj.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-29", "2025-02-28", "2025-03-31"]),
            "country": ["JP"] * 3,
            "provider": ["BOJ"] * 3,
            "series_id": ["BS01.MABJMTA"] * 3,
            "component": ["boj_total_assets"] * 3,
            "value": [6_000_000.0, 6_600_000.0, 6_732_000.0],
            "unit": ["100 Million Yen"] * 3,
            "frequency": ["Monthly, End of Period"] * 3,
            "retrieved_at": [pd.Timestamp("2025-04-05", tz=UTC)] * 3,
        }
    ).to_parquet(path, index=False)

    result = load_boj_data(path)
    latest = latest_boj_readings(result).iloc[0]

    assert result["value_jpy_billions"].tolist() == [600_000.0, 660_000.0, 673_200.0]
    assert latest["change_jpy_billions"] == 13_200.0
    assert latest["growth_yoy"] == pytest.approx(0.122)


def test_load_boj_data_rejects_wrong_provider(tmp_path: Path) -> None:
    path = tmp_path / "boj.parquet"
    frame = _processed_frame().iloc[:1].copy()
    frame["country"] = "JP"
    frame["provider"] = "FRED"
    frame["unit"] = "100 Million Yen"
    frame.to_parquet(path, index=False)

    with pytest.raises(DashboardDataError, match="unexpected provider"):
        load_boj_data(path)


def test_load_ecb_data_and_latest_changes(tmp_path: Path) -> None:
    path = tmp_path / "ecb.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-31", "2025-01-31", "2025-02-28"]),
            "country": ["EA"] * 3,
            "provider": ["ECB"] * 3,
            "series_id": ["BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E"] * 3,
            "component": ["eurosystem_total_assets"] * 3,
            "value": [9_000_000.0, 9_900_000.0, 10_098_000.0],
            "unit": ["Millions of Euro"] * 3,
            "frequency": ["Monthly, End of Period"] * 3,
            "retrieved_at": [pd.Timestamp("2025-03-20", tz=UTC)] * 3,
        }
    ).to_parquet(path, index=False)

    result = load_ecb_data(path)
    latest = latest_ecb_readings(result).iloc[0]

    assert result["value_eur_billions"].tolist() == [9_000.0, 9_900.0, 10_098.0]
    assert latest["change_eur_billions"] == 198.0
    assert latest["growth_yoy"] == pytest.approx(0.122)


def test_load_ecb_data_rejects_mixed_currency(tmp_path: Path) -> None:
    path = tmp_path / "ecb.parquet"
    frame = _processed_frame().iloc[:1].copy()
    frame["country"] = "EA"
    frame["provider"] = "ECB"
    frame["unit"] = "Millions of U.S. Dollars"
    frame.to_parquet(path, index=False)

    with pytest.raises(DashboardDataError, match="unexpected unit"):
        load_ecb_data(path)


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


def test_load_point_in_time_comparison_validates_exact_date_policy(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_vintage_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    path = tmp_path / "point_in_time.parquet"
    pd.DataFrame(
        {
            "information_date": pd.to_datetime(["2024-01-31"]),
            "signal_observation_date": pd.to_datetime(["2024-01-24"]),
            "model_id": ["model_a"],
            "model_name": ["Model A"],
            "vintage_ogli": [40.0],
            "vintage_momentum_score": [-0.2],
            "vintage_regime": ["Below normal"],
            "current_ogli": [44.0],
            "current_momentum_score": [-0.1],
            "current_regime": ["Below normal"],
            "ogli_revision": [4.0],
            "momentum_revision": [0.1],
            "comparison_policy": ["same_observation_date"],
        }
    ).to_parquet(path, index=False)

    result = support.load_point_in_time_comparison(path)

    assert result.loc[0, "ogli_revision"] == 4.0
    assert result.loc[0, "signal_observation_date"] == pd.Timestamp("2024-01-24")


def test_load_point_in_time_market_outputs(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_pit_market_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    pair_path = tmp_path / "pairs.parquet"
    summary_path = tmp_path / "summary.parquet"
    pair = {column: None for column in support.POINT_IN_TIME_MARKET_PAIR_COLUMNS}
    pair.update(
        {
            "information_date": pd.Timestamp("2024-01-31"),
            "signal_observation_date": pd.Timestamp("2024-01-24"),
            "signal_available_date": pd.Timestamp("2024-02-07"),
            "model_id": "model_b",
            "model_name": "Model B",
            "vintage_ogli": 55.0,
            "vintage_momentum_score": 0.1,
            "vintage_regime": "Neutral",
            "market_id": "bitcoin",
            "series_id": "btc.PriceUSD",
            "provider": "Coin Metrics",
            "unit": "U.S. Dollars per Bitcoin",
            "source_frequency": "Daily",
            "publication_lag_weeks": 1,
            "horizon_months": 3,
            "start_target_date": pd.Timestamp("2024-02-07"),
            "start_observation_date": pd.Timestamp("2024-02-07"),
            "start_value": 43_000.0,
            "end_target_date": pd.Timestamp("2024-05-07"),
            "end_observation_date": pd.Timestamp("2024-05-07"),
            "end_value": 63_000.0,
            "market_return": 63_000 / 43_000 - 1,
            "is_non_overlapping": True,
            "classification": "statistical_transformation",
        }
    )
    pd.DataFrame([pair]).to_parquet(pair_path, index=False)
    summary = {column: None for column in support.POINT_IN_TIME_MARKET_SUMMARY_COLUMNS}
    summary.update(
        {
            "model_id": "model_b",
            "model_name": "Model B",
            "market_id": "bitcoin",
            "series_id": "btc.PriceUSD",
            "publication_lag_weeks": 1,
            "horizon_months": 3,
            "sample_policy": "overlapping",
            "observations": 12,
            "correlation": 0.2,
            "mean_return": 0.1,
            "median_return": 0.08,
            "positive_share": 0.6,
            "classification": "descriptive_statistic",
        }
    )
    pd.DataFrame([summary]).to_parquet(summary_path, index=False)

    loaded_pairs = support.load_point_in_time_market_pairs(pair_path)
    loaded_summary = support.load_point_in_time_market_summary(summary_path)

    assert loaded_pairs.loc[0, "market_return"] == pytest.approx(63_000 / 43_000 - 1)
    assert loaded_summary.loc[0, "correlation"] == 0.2


def test_freshness_status_flags_old_observations() -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_freshness_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    frame = pd.DataFrame({"date": pd.to_datetime(["2024-01-03", "2024-01-10"])})

    status = support.assess_freshness(
        frame,
        as_of=pd.Timestamp("2024-01-25", tz="UTC"),
        max_age_days=14,
    )

    assert status.latest_date == pd.Timestamp("2024-01-10")
    assert status.age_days == 15
    assert status.is_stale


def test_load_snapshot_manifest_validates_point_in_time_metadata(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_manifest_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classification": "snapshot_provenance",
                "generated_at": "2024-01-11T12:00:00+00:00",
                "pipeline_version": "0.1.0",
                "source_commit": "abc123",
                "working_tree_dirty": False,
                "snapshot_count": 1,
                "files": {
                    "sample.parquet": {
                        "sha256": "a" * 64,
                        "rows": 2,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = support.load_snapshot_manifest(path)

    assert manifest["source_commit"] == "abc123"
    assert manifest["snapshot_count"] == 1


def test_loads_published_bitcoin_research_snapshots() -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_bitcoin_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    snapshots = Path(__file__).resolve().parents[1] / "data" / "reference"

    outcomes = support.load_bitcoin_outcomes(
        snapshots / "us_point_in_time_bitcoin_outcomes_snapshot.parquet"
    )
    regimes = support.load_bitcoin_regime_summary(
        snapshots / "us_point_in_time_bitcoin_regimes_snapshot.parquet"
    )
    revisions = support.load_bitcoin_revision_summary(
        snapshots / "us_point_in_time_bitcoin_revisions_snapshot.parquet"
    )
    contrasts = support.load_bitcoin_contrast_summary(
        snapshots / "us_point_in_time_bitcoin_contrasts_snapshot.parquet"
    )

    assert set(outcomes["market_id"]) == {"bitcoin"}
    assert regimes["mean_return_ci_lower"].notna().any()
    assert set(regimes.loc[regimes["specification_role"] == "primary", "model_id"]) == {"model_b"}
    assert revisions["regime_agreement_share"].between(0, 1).all()
    primary_contrasts = contrasts.loc[contrasts["specification_role"] == "primary"]
    assert set(primary_contrasts["model_id"]) == {"model_b"}
    assert set(primary_contrasts["horizon_months"]) == {1, 3, 6, 12}


def test_bitcoin_snapshot_loader_rejects_impossible_path_statistic(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location(
        "dashboard_support_bitcoin_invalid_test", support_path
    )
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    source = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "reference"
        / "us_point_in_time_bitcoin_outcomes_snapshot.parquet"
    )
    frame = pd.read_parquet(source).head(1)
    frame.loc[:, "maximum_drawdown_from_peak"] = 0.10
    invalid_path = tmp_path / "invalid_bitcoin_outcomes.parquet"
    frame.to_parquet(invalid_path, index=False)

    with pytest.raises(support.DashboardDataError, match="impossible path statistics"):
        support.load_bitcoin_outcomes(invalid_path)
