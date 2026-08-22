from datetime import UTC
from pathlib import Path

import pandas as pd

from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.pipeline import run_pipeline


def test_pipeline_writes_processed_parquet(monkeypatch, tmp_path: Path) -> None:
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
      description: Measured test data
      unit: Millions of U.S. Dollars
      frequency: Weekly, As of Wednesday
      seasonal_adjustment: Not Seasonally Adjusted
      start: '2024-01-01'
      source: Federal Reserve
      source_url: https://fred.stlouisfed.org/series/WALCL
""".strip()
    )
    expected = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03"]),
            "country": ["US"],
            "provider": ["FRED"],
            "series_id": ["WALCL"],
            "component": ["fed_assets"],
            "value": [6_794_581.0],
            "unit": ["Millions of U.S. Dollars"],
            "frequency": ["Weekly, As of Wednesday"],
            "retrieved_at": [pd.Timestamp("2024-01-11", tz=UTC)],
        }
    )

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(
        "open_global_liquidity.pipeline.FredProvider.fetch_definition",
        lambda self, definition, **kwargs: expected,
    )

    output_path = run_pipeline(project_root=tmp_path, publish_dashboard_snapshot=True)
    result = pd.read_parquet(output_path)
    snapshot = pd.read_parquet(tmp_path / "data" / "reference" / "us_fred_series_snapshot.parquet")

    assert output_path == tmp_path / "data" / "processed" / "us_fred_series.parquet"
    assert result.columns.tolist() == STANDARD_COLUMNS
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(snapshot, expected)
