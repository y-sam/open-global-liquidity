from datetime import UTC
from io import BytesIO
from pathlib import Path

import httpx
import pandas as pd

from open_global_liquidity.config import load_series_config
from open_global_liquidity.data.world_bank import WorldBankProvider


def _workbook_bytes() -> bytes:
    rows = pd.DataFrame(
        {
            "period": ["2024M01", "2024M02"],
            **{f"unused_{index}": [index, index] for index in range(1, 69)},
            "Gold": [2_034.0, 2_044.0],
        }
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        rows.to_excel(writer, sheet_name="Monthly Prices", index=False, startrow=4)
    return output.getvalue()


def test_world_bank_provider_parses_monthly_gold(httpx_mock, tmp_path: Path) -> None:
    httpx_mock.add_response(content=_workbook_bytes())
    definition = next(
        item
        for item in load_series_config(Path("config/series.yaml"))
        if item.series_id == "CMO-GOLD-MONTHLY"
    )
    provider = WorldBankProvider(
        cache_dir=tmp_path,
        client=httpx.Client(),
    )

    result = provider.fetch_definition(definition, start="2024-01-01")

    assert result["date"].tolist() == [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29")]
    assert result["value"].tolist() == [2_034.0, 2_044.0]
    assert result["provider"].eq("World Bank").all()
    assert result["retrieved_at"].map(lambda value: value.tzinfo == UTC).all()
