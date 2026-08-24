from datetime import UTC
from pathlib import Path

import pandas as pd

from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.fred import VINTAGE_COLUMNS
from open_global_liquidity.vintage_pipeline import run_vintage_capture


def test_vintage_pipeline_writes_separate_as_of_dataset(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_dir.joinpath("series.yaml").write_text(
        """
US:
  liquidity:
    fed_assets:
      classification: measured_data
      provider: fred
      series_id: WALCL
      component: fed_assets
      title: Fed assets
      description: Test series
      unit: Millions of U.S. Dollars
      frequency: Weekly, As of Wednesday
      seasonal_adjustment: Not Seasonally Adjusted
      start: '2024-01-01'
      source: Federal Reserve
      source_url: https://fred.stlouisfed.org/series/WALCL
""".strip(),
        encoding="utf-8",
    )

    def fake_fetch_vintage(_provider, definition, **kwargs):
        assert kwargs["vintage_date"] == pd.Timestamp("2024-01-11").date()
        return pd.DataFrame(
            {
                "observation_date": pd.to_datetime(["2024-01-03"]),
                "vintage_date": pd.to_datetime(["2024-01-11"]),
                "country": ["US"],
                "provider": ["ALFRED"],
                "series_id": [definition.series_id],
                "component": [definition.component],
                "value": [6_794_581.0],
                "unit": [definition.unit],
                "frequency": [definition.frequency],
                "realtime_start": ["2024-01-11"],
                "realtime_end": ["9999-12-31"],
                "retrieved_at": [pd.Timestamp("2024-01-12", tz=UTC)],
            }
        )[VINTAGE_COLUMNS]

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(
        "open_global_liquidity.vintage_pipeline.FredProvider.fetch_vintage_definition",
        fake_fetch_vintage,
    )

    def fake_fetch_current(_provider, definition, **_kwargs):
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-03"]),
                "country": ["US"],
                "provider": ["FRED"],
                "series_id": [definition.series_id],
                "component": [definition.component],
                "value": [6_794_582.0],
                "unit": [definition.unit],
                "frequency": [definition.frequency],
                "retrieved_at": [pd.Timestamp("2024-01-13", tz=UTC)],
            }
        )[STANDARD_COLUMNS]

    monkeypatch.setattr(
        "open_global_liquidity.vintage_pipeline.FredProvider.fetch_definition",
        fake_fetch_current,
    )

    path = run_vintage_capture(as_of="2024-01-11", project_root=tmp_path, compare_current=True)
    result = pd.read_parquet(path)
    revisions = pd.read_parquet(path.parent / "revision_comparison_to_current.parquet")

    assert path == (
        tmp_path
        / "data"
        / "vintages"
        / "fred"
        / "as_of=2024-01-11"
        / "us_liquidity_vintage.parquet"
    )
    assert result.columns.tolist() == VINTAGE_COLUMNS
    assert result["provider"].item() == "ALFRED"
    assert revisions["revision"].item() == 1.0
