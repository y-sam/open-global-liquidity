import json
from datetime import UTC
from pathlib import Path

import pandas as pd

from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.pipeline import run_pipeline


def _write_test_config(project_root: Path) -> None:
    config_dir = project_root / "config"
    config_dir.mkdir()
    series = {
        "fed_assets": ("WALCL", "Millions of U.S. Dollars", "Weekly, As of Wednesday"),
        "treasury_general_account": (
            "WDTGAL",
            "Millions of U.S. Dollars",
            "Weekly, As of Wednesday",
        ),
        "overnight_reverse_repo": ("RRPONTSYD", "Billions of U.S. Dollars", "Daily"),
        "reserve_balances": (
            "WRBWFRBL",
            "Millions of U.S. Dollars",
            "Weekly, As of Wednesday",
        ),
        "bitcoin": ("btc.PriceUSD", "U.S. Dollars per Bitcoin", "Daily"),
    }
    blocks = []
    for component, (series_id, unit, frequency) in series.items():
        blocks.append(
            f"""    {component}:
      classification: measured_data
      provider: {"coinmetrics" if component == "bitcoin" else "fred"}
      series_id: {series_id}
      component: {component}
      title: Test {component}
      description: Measured test data
      unit: {unit}
      frequency: {frequency}
      seasonal_adjustment: Not Seasonally Adjusted
      start: '2024-01-01'
      source: Test provider
      source_url: https://example.com/{series_id}"""
        )
    liquidity_blocks = [block for block in blocks if "    bitcoin:" not in block]
    market_block = next(block for block in blocks if "    bitcoin:" in block)
    config_dir.joinpath("series.yaml").write_text(
        "US:\n  liquidity:\n" + "\n".join(liquidity_blocks) + "\n  markets:\n" + market_block,
        encoding="utf-8",
    )
    config_dir.joinpath("model.yaml").write_text(
        """
weekly_alignment:
  classification: model_assumption
  canonical_frequency: W-WED
  observation_day: Wednesday
  output_unit: Millions of U.S. Dollars
  daily_asof_components: [overnight_reverse_repo]
  daily_asof_max_staleness_days: 7
  weekly_missing_policy: exact_only
liquidity_models:
  model_a:
    name: Model A
    classification: model_assumption
    formula: fed_assets
    description: Test model A
    terms: {fed_assets: 1.0}
  model_b:
    name: Model B
    classification: model_assumption
    formula: fed_assets - treasury_general_account - overnight_reverse_repo
    description: Test model B
    terms: {fed_assets: 1.0, treasury_general_account: -1.0, overnight_reverse_repo: -1.0}
  model_c:
    name: Model C
    classification: model_assumption
    formula: reserve_balances
    description: Test model C
    terms: {reserve_balances: 1.0}
ogli:
  classification: statistical_transformation
  description: Test OGLI
  normalization:
    classification: statistical_transformation
    default_mode: expanding
    min_periods: 2
  momentum_weights:
    classification: model_assumption
    growth_3m_annualized: 0.6
    growth_12m_yoy: 0.4
  regimes:
    classification: model_assumption
    thresholds:
      - {label: Strong contraction, max: 10}
      - {label: Contraction, max: 30}
      - {label: Below normal, max: 45}
      - {label: Neutral, max: 55}
      - {label: Above normal, max: 70}
      - {label: Expansion, max: 90}
      - {label: Strong expansion, max: 100}
market_alignment:
  classification: model_assumption
  canonical_frequency: W-WED
  observation_day: Wednesday
  daily_asof_components: [bitcoin]
  daily_asof_max_staleness_days: 7
  missing_policy: latest_prior_close
market_analysis:
  classification: statistical_transformation
  liquidity_signal: momentum_score
  publication_lag_policy: observation_and_available_information
  signal_availability_lag_weeks: 1
  forward_horizons_weeks: [0, 4, 8, 12, 26, 52]
  correlation_min_periods: 2
  non_overlapping_min_periods: 2
  confidence_level: 0.95
  research_subperiods:
    classification: model_assumption
    periods:
      - {id: test_period, label: Test period, start: '2024-01-01', end: null}
  rolling_window_weeks: 2
  rolling_min_periods: 2
  description: Test market analysis
""".strip(),
        encoding="utf-8",
    )


def test_pipeline_writes_source_weekly_and_model_parquet(monkeypatch, tmp_path: Path) -> None:
    _write_test_config(tmp_path)
    values = {
        "WALCL": (8_000_000.0, "Millions of U.S. Dollars"),
        "WDTGAL": (500_000.0, "Millions of U.S. Dollars"),
        "RRPONTSYD": (1_000.0, "Billions of U.S. Dollars"),
        "WRBWFRBL": (3_000_000.0, "Millions of U.S. Dollars"),
        "btc.PriceUSD": (60_000.0, "U.S. Dollars per Bitcoin"),
    }

    def fake_fetch(_provider, definition, **_kwargs):
        value, unit = values[definition.series_id]
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-03"]),
                "country": ["US"],
                "provider": [definition.provider],
                "series_id": [definition.series_id],
                "component": [definition.component],
                "value": [value],
                "unit": [unit],
                "frequency": [definition.frequency],
                "retrieved_at": [pd.Timestamp("2024-01-11", tz=UTC)],
            }
        )

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr("open_global_liquidity.pipeline.FredProvider.fetch_definition", fake_fetch)
    monkeypatch.setattr(
        "open_global_liquidity.pipeline.CoinMetricsProvider.fetch_definition", fake_fetch
    )

    output_path = run_pipeline(project_root=tmp_path, publish_dashboard_snapshot=True)
    source = pd.read_parquet(output_path)
    weekly = pd.read_parquet(tmp_path / "data" / "processed" / "us_liquidity_weekly.parquet")
    models = pd.read_parquet(tmp_path / "data" / "processed" / "us_liquidity_models.parquet")
    ogli = pd.read_parquet(tmp_path / "data" / "processed" / "us_ogli.parquet")
    market_source = pd.read_parquet(tmp_path / "data" / "processed" / "us_market_series.parquet")
    market_weekly = pd.read_parquet(tmp_path / "data" / "processed" / "us_market_weekly.parquet")
    market_returns = pd.read_parquet(tmp_path / "data" / "processed" / "us_market_returns.parquet")
    comparisons = pd.read_parquet(
        tmp_path / "data" / "processed" / "us_liquidity_market_comparisons.parquet"
    )
    correlations = pd.read_parquet(
        tmp_path / "data" / "processed" / "us_liquidity_market_correlations.parquet"
    )
    subperiods = pd.read_parquet(
        tmp_path / "data" / "processed" / "us_liquidity_market_subperiods.parquet"
    )
    snapshot_dir = tmp_path / "data" / "reference"
    source_snapshot = pd.read_parquet(snapshot_dir / "us_fred_series_snapshot.parquet")
    weekly_snapshot = pd.read_parquet(snapshot_dir / "us_liquidity_weekly_snapshot.parquet")
    model_snapshot = pd.read_parquet(snapshot_dir / "us_liquidity_models_snapshot.parquet")
    ogli_snapshot = pd.read_parquet(snapshot_dir / "us_ogli_snapshot.parquet")
    correlation_snapshot = pd.read_parquet(
        snapshot_dir / "us_liquidity_market_correlations_snapshot.parquet"
    )
    comparison_snapshot = pd.read_parquet(
        snapshot_dir / "us_liquidity_market_comparisons_snapshot.parquet"
    )
    subperiod_snapshot = pd.read_parquet(
        snapshot_dir / "us_liquidity_market_subperiods_snapshot.parquet"
    )
    manifest = json.loads(
        snapshot_dir.joinpath("dashboard_snapshot_manifest.json").read_text(encoding="utf-8")
    )

    assert output_path == tmp_path / "data" / "processed" / "us_fred_series.parquet"
    assert source.columns.tolist() == STANDARD_COLUMNS
    assert len(source) == 4
    assert len(weekly) == 4
    assert weekly.loc[weekly["component"] == "overnight_reverse_repo", "value"].item() == 1_000_000
    model_values = models.set_index("model_id")["value"]
    assert model_values.to_dict() == {
        "model_a": 8_000_000.0,
        "model_b": 6_500_000.0,
        "model_c": 3_000_000.0,
    }
    pd.testing.assert_frame_equal(source_snapshot, source)
    pd.testing.assert_frame_equal(weekly_snapshot, weekly)
    pd.testing.assert_frame_equal(model_snapshot, models)
    assert len(ogli) == 3
    assert ogli["ogli"].isna().all()
    assert set(ogli["zscore_mode"]) == {"expanding"}
    pd.testing.assert_frame_equal(ogli_snapshot, ogli)
    assert market_source["series_id"].unique().tolist() == ["btc.PriceUSD"]
    assert market_weekly["value"].item() == 60_000.0
    assert len(market_returns) == 6
    assert len(comparisons) == 18
    assert len(correlations) == 18
    assert len(subperiods) == 18
    assert set(comparisons["analysis_mode"]) == {"observation_date"}
    pd.testing.assert_frame_equal(correlation_snapshot, correlations)
    pd.testing.assert_frame_equal(comparison_snapshot, comparisons)
    pd.testing.assert_frame_equal(subperiod_snapshot, subperiods)
    assert manifest["snapshot_count"] == 11
    assert set(manifest["files"]) == {path.name for path in snapshot_dir.glob("*.parquet")}
    assert manifest["files"]["us_liquidity_market_subperiods_snapshot.parquet"]["rows"] == 18
    assert snapshot_dir.joinpath("us_market_series_snapshot.parquet").is_file()
    assert snapshot_dir.joinpath("us_market_weekly_snapshot.parquet").is_file()
    assert snapshot_dir.joinpath("us_market_returns_snapshot.parquet").is_file()
