from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.treasury import (
    TreasuryFiscalDataError,
    TreasuryFiscalDataProvider,
)


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="US",
        group="collateral",
        name="marketable_treasury_debt_public",
        classification="measured_data",
        provider="treasury",
        series_id="MSPD.TABLE1.TOTAL_MARKETABLE.DEBT_HELD_PUBLIC",
        component="marketable_treasury_debt_public",
        title="Total Marketable Treasury Securities Held by the Public",
        description="Test Treasury data",
        unit="Millions of U.S. Dollars",
        frequency="Monthly, End of Period",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2024-01-31").date(),
        source="U.S. Treasury Fiscal Data",
        source_url="https://fiscaldata.treasury.gov/",
    )


def test_fetch_standardizes_total_marketable_debt(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                request=request,
                json={
                    "data": [
                        {
                            "record_date": "2024-01-31",
                            "security_type_desc": "Total Marketable",
                            "debt_held_public_mil_amt": "25000000.25",
                        },
                        {
                            "record_date": "2024-02-29",
                            "security_type_desc": "Total Marketable",
                            "debt_held_public_mil_amt": "25200000.50",
                        },
                    ]
                },
            )
        )
    )
    provider = TreasuryFiscalDataProvider(cache_dir=tmp_path, client=client)

    result = provider.fetch_definition(_definition(), start="2024-02-01")

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2024-02-29")]
    assert result["value"].tolist() == [25_200_000.50]
    assert result["provider"].unique().tolist() == ["U.S. Treasury Fiscal Data"]
    assert (tmp_path / "mspd_total_marketable_public.parquet").is_file()


def test_fetch_rejects_wrong_security_type(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                request=request,
                json={
                    "data": [
                        {
                            "record_date": "2024-01-31",
                            "security_type_desc": "Marketable",
                            "debt_held_public_mil_amt": "1",
                        }
                    ]
                },
            )
        )
    )

    with pytest.raises(TreasuryFiscalDataError, match="unexpected security type"):
        TreasuryFiscalDataProvider(cache_dir=tmp_path, client=client).fetch_definition(
            _definition()
        )
