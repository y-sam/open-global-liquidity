import pandas as pd

from open_global_liquidity.analysis.data_quality import build_data_quality_inventory


def test_inventory_preserves_metadata_limits_without_scoring_freshness() -> None:
    inventory = build_data_quality_inventory(
        {
            "series.parquet": pd.DataFrame(
                {
                    "date": ["2025-01-01"],
                    "value": [1.0],
                    "retrieved_at": ["2025-01-02T00:00:00Z"],
                }
            ),
            "summary.parquet": pd.DataFrame({"label": ["x"], "value": [None]}),
        }
    ).set_index("filename")
    assert inventory.loc["series.parquet", "metadata_status"] == (
        "observation_and_retrieval_metadata"
    )
    assert inventory.loc["summary.parquet", "metadata_status"] == "structural_or_summary_table"
    assert inventory.loc["summary.parquet", "null_cells"] == 1
    assert "freshness_score" not in inventory.columns
