import importlib.util
import json
from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from open_global_liquidity.dashboard import (
    DashboardDataError,
    build_central_bank_index_comparison,
    latest_boe_readings,
    latest_boj_readings,
    latest_ecb_readings,
    latest_model_readings,
    latest_pboc_readings,
    latest_readings,
    load_boe_data,
    load_boj_data,
    load_dashboard_data,
    load_ecb_data,
    load_liquidity_model_data,
    load_pboc_data,
    resolve_dashboard_data_path,
)


def test_load_pboc_data_and_latest_changes(tmp_path: Path) -> None:
    path = tmp_path / "pboc.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-29", "2025-02-28", "2025-03-31"]),
            "country": ["CN"] * 3,
            "provider": ["PBOC"] * 3,
            "series_id": ["PBOC.BSMA.TOTAL_ASSETS"] * 3,
            "component": ["pboc_total_assets"] * 3,
            "value": [400_000.0, 440_000.0, 448_800.0],
            "unit": ["100 Million Yuan"] * 3,
            "frequency": ["Monthly, End of Period"] * 3,
            "retrieved_at": [pd.Timestamp("2025-04-15", tz=UTC)] * 3,
        }
    ).to_parquet(path, index=False)

    result = load_pboc_data(path)
    latest = latest_pboc_readings(result).iloc[0]

    assert result["value_cny_billions"].tolist() == [40_000.0, 44_000.0, 44_880.0]
    assert latest["change_cny_billions"] == 880.0
    assert latest["growth_yoy"] == pytest.approx(0.122)


def test_load_bis_china_data_is_already_in_cny_billions(tmp_path: Path) -> None:
    path = tmp_path / "china_bis.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-31", "2025-02-28"]),
            "country": ["CN", "CN"],
            "provider": ["BIS", "BIS"],
            "series_id": ["BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N"] * 2,
            "component": ["china_central_bank_total_assets"] * 2,
            "value": [46_657.47, 47_020.53],
            "unit": ["Billions of Chinese Yuan"] * 2,
            "frequency": ["Monthly, End of Period"] * 2,
            "retrieved_at": [pd.Timestamp("2025-03-01", tz=UTC)] * 2,
        }
    ).to_parquet(path, index=False)

    result = load_pboc_data(path)
    latest = latest_pboc_readings(result).iloc[0]

    assert result["value_cny_billions"].tolist() == [46_657.47, 47_020.53]
    assert latest["provider"] == "BIS"
    assert latest["change_cny_billions"] == pytest.approx(363.06)


def test_central_bank_comparison_rebases_each_native_series_independently() -> None:
    comparison = build_central_bank_index_comparison(
        {
            "Bank A": pd.DataFrame(
                {"date": pd.to_datetime(["2024-01-31", "2024-02-29"]), "native_value": [10, 12]}
            ),
            "Bank B": pd.DataFrame(
                {"date": pd.to_datetime(["2024-02-29", "2024-03-31"]), "native_value": [200, 180]}
            ),
        },
        start="2024-01-01",
    )

    by_bank = comparison.groupby("central_bank")["index"].apply(list).to_dict()
    assert by_bank["Bank A"] == [100.0, 120.0]
    assert by_bank["Bank B"] == [100.0, 90.0]


def test_load_boe_data_and_latest_changes(tmp_path: Path) -> None:
    path = tmp_path / "boe.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-03-06", "2025-03-05", "2025-03-12"]),
            "country": ["GB"] * 3,
            "provider": ["BOE"] * 3,
            "series_id": ["RPQB75A"] * 3,
            "component": ["boe_total_assets"] * 3,
            "value": [900_000.0, 990_000.0, 1_009_800.0],
            "unit": ["Millions of Sterling"] * 3,
            "frequency": ["Quarterly"] * 3,
            "retrieved_at": [pd.Timestamp("2025-03-13", tz=UTC)] * 3,
        }
    ).to_parquet(path, index=False)

    result = load_boe_data(path)
    latest = latest_boe_readings(result).iloc[0]

    assert result["value_gbp_billions"].tolist() == pytest.approx([900.0, 990.0, 1_009.8])
    assert latest["change_gbp_billions"] == pytest.approx(19.8)
    assert latest["growth_yoy"] == pytest.approx(0.122)


def test_load_boe_data_rejects_wrong_unit(tmp_path: Path) -> None:
    path = tmp_path / "boe.parquet"
    frame = _processed_frame().iloc[:1].copy()
    frame["country"] = "GB"
    frame["provider"] = "BOE"
    frame["unit"] = "Millions of U.S. Dollars"
    frame.to_parquet(path, index=False)

    with pytest.raises(DashboardDataError, match="unexpected unit"):
        load_boe_data(path)


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


def test_loads_published_global_aggregate_snapshots() -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_global_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    snapshots = Path(__file__).resolve().parents[1] / "data" / "reference"

    aggregate = support.load_global_central_bank_aggregate(
        snapshots / "global_central_bank_assets_snapshot.parquet"
    )
    detail = support.load_global_central_bank_detail(
        snapshots / "global_central_bank_assets_detail_snapshot.parquet"
    )
    global_pairs = support.load_global_bitcoin_pairs(
        snapshots / "global_central_bank_bitcoin_pairs_snapshot.parquet"
    )
    global_summary = support.load_global_bitcoin_summary(
        snapshots / "global_central_bank_bitcoin_summary_snapshot.parquet"
    )
    cross_border = support.load_cross_border_credit(
        snapshots / "global_cross_border_credit_indicators_snapshot.parquet"
    )
    currency_context = support.load_foreign_currency_credit_context(
        snapshots / "global_foreign_currency_credit_context_snapshot.parquet"
    )
    auxiliary_pairs = support.load_auxiliary_bitcoin_pairs(
        snapshots / "global_auxiliary_bitcoin_pairs_snapshot.parquet"
    )
    auxiliary_summary = support.load_auxiliary_bitcoin_summary(
        snapshots / "global_auxiliary_bitcoin_summary_snapshot.parquet"
    )
    availability = support.load_global_availability_registry(
        snapshots / "global_availability_registry_snapshot.parquet"
    )
    model_h = support.load_model_h(snapshots / "global_model_h_snapshot.parquet")
    signal_map = support.load_liquidity_signal_map(
        snapshots / "liquidity_signal_map_snapshot.parquet"
    )
    quality = support.load_data_quality_inventory(
        snapshots / "data_quality_inventory_snapshot.parquet"
    )
    private_liquidity = support.load_private_liquidity(
        snapshots / "us_private_liquidity_indicators_snapshot.parquet"
    )

    assert aggregate["component_count"].eq(5).all()
    assert aggregate["classification"].eq("model_assumption").all()
    assert aggregate["global_cb_index"].dropna().between(0, 100).all()
    assert aggregate["global_cb_index"].notna().any()
    global_display = support.prepare_global_index_display(aggregate)
    assert global_display["growth_12m_yoy"].equals(
        aggregate.loc[aggregate["global_cb_index"].notna(), "growth_yoy"]
    )
    assert global_display["index_value"].notna().all()
    assert cross_border["offshore_dollar_credit_index"].dropna().between(0, 100).all()
    assert cross_border["provider"].eq("BIS").all()
    assert currency_context["component"].nunique() == 3
    assert currency_context["model_role"].eq("context_only_not_model_input").all()
    assert set(auxiliary_pairs["model_id"]) == {
        "offshore_dollar_credit",
        "us_private_liquidity",
    }
    assert auxiliary_summary["specification_role"].eq("primary").sum() == 2
    assert len(availability) == 9
    assert availability["point_in_time_status"].eq("lag_adjusted_current_vintage").all()
    assert model_h["model_h_index"].between(0, 100).all()
    assert model_h["result_status"].eq("post_specification_descriptive").all()
    assert signal_map["channel"].nunique() == 4
    assert signal_map["aggregation_status"].eq("not_aggregated").all()
    assert quality["filename"].nunique() >= 46
    assert quality["duplicate_rows"].ge(0).all()
    assert private_liquidity["private_liquidity_index"].dropna().between(0, 100).all()
    assert (
        private_liquidity.loc[
            private_liquidity["private_liquidity_index"].notna(), "private_liquidity_regime"
        ]
        .notna()
        .all()
    )
    assert len(aggregate) >= 290
    assert aggregate["date"].min() == pd.Timestamp("2002-01-31")
    assert detail.groupby("date")["central_bank"].nunique().eq(5).all()
    assert set(detail["fx_component"]) == {
        "USD",
        "usd_per_euro",
        "yen_per_usd",
        "usd_per_sterling",
        "yuan_per_usd",
    }
    assert global_pairs["signal_date"].nunique() >= 190
    assert set(global_summary["sample_policy"]) == {"overlapping", "non_overlapping"}


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


def test_load_collateral_conditions_preserves_auditable_model_metadata(tmp_path: Path) -> None:
    support_path = Path(__file__).resolve().parents[1] / "app" / "dashboard_support.py"
    spec = importlib.util.spec_from_file_location("dashboard_support_collateral_test", support_path)
    assert spec is not None and spec.loader is not None
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    path = tmp_path / "collateral.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-31", "2024-02-29"]),
            "gross_marketable_collateral_millions": [26_000_000.0, 26_200_000.0],
            "fed_treasury_holdings_millions": [5_000_000.0, 4_950_000.0],
            "private_collateral_proxy_millions": [21_000_000.0, 21_250_000.0],
            "collateral_supply_growth_yoy": [0.05, 0.06],
            "funding_spread_bps": [1.0, 2.0],
            "treasury_volatility_bps": [90.0, 95.0],
            "z_collateral_supply_growth_yoy": [0.2, 0.3],
            "z_funding_spread_bps": [-0.1, 0.1],
            "z_treasury_volatility_bps": [0.0, 0.2],
            "collateral_conditions_score": [0.11, 0.03],
            "collateral_conditions_index": [54.38, 51.20],
            "collateral_regime": ["Neutral", "Neutral"],
            "model_name": ["Open Collateral Conditions Score"] * 2,
            "model_classification": ["model_assumption"] * 2,
            "normalization_mode": ["expanding"] * 2,
            "normalization_min_periods": [24, 24],
            "retrieved_at": [pd.Timestamp("2024-03-01", tz=UTC)] * 2,
        }
    ).to_parquet(path, index=False)

    loaded = support.load_collateral_conditions(path)

    assert loaded["date"].tolist() == list(pd.to_datetime(["2024-01-31", "2024-02-29"]))
    assert loaded["collateral_conditions_index"].tolist() == [54.38, 51.20]
    assert set(loaded["model_classification"]) == {"model_assumption"}


def test_collateral_page_degrades_cleanly_without_snapshot(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OGLI_DATA_ROOT", str(tmp_path / "data"))
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(app_path, default_timeout=20)
    app._page_hash = calc_hash("collateral-conditions")
    app.run()

    assert not app.exception
    assert app.title[0].value == "Collateral conditions"
    assert any("has not been generated" in message.value for message in app.info)


def test_offshore_dollar_page_renders_published_snapshot() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(app_path, default_timeout=20)
    app._page_hash = calc_hash("offshore-dollar-credit")
    app.run()

    assert not app.exception
    assert app.title[0].value == "Offshore dollar credit"
    assert any(metric.label == "Credit momentum index" for metric in app.metric)
    assert any(metric.label == "Primary correlation" for metric in app.metric)


def test_private_liquidity_page_renders_published_snapshot() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(app_path, default_timeout=20)
    app._page_hash = calc_hash("private-liquidity")
    app.run()

    assert not app.exception
    assert app.title[0].value == "US private liquidity"
    assert any(metric.label == "Private liquidity index" for metric in app.metric)
    assert any(metric.label == "Primary correlation" for metric in app.metric)
