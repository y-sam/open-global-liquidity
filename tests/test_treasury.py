from dataclasses import replace
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
                            "security_class_desc": "_",
                            "debt_held_public_mil_amt": "25000000.25",
                        },
                        {
                            "record_date": "2024-02-29",
                            "security_type_desc": "Total Marketable",
                            "security_class_desc": "_",
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
    assert (tmp_path / "mspd_marketable_treasury_debt_public.parquet").is_file()


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
                            "security_class_desc": "Notes",
                            "debt_held_public_mil_amt": "1",
                        }
                    ]
                },
            )
        )
    )

    with pytest.raises(TreasuryFiscalDataError, match="unexpected security class"):
        TreasuryFiscalDataProvider(cache_dir=tmp_path, client=client).fetch_definition(
            _definition()
        )


def test_fetch_selects_exact_marketable_security_class(tmp_path: Path) -> None:
    definition = replace(
        _definition(),
        name="marketable_treasury_bills_public",
        series_id="MSPD.TABLE1.MARKETABLE.BILLS.DEBT_HELD_PUBLIC",
        component="marketable_treasury_bills_public",
    )

    def response(request: httpx.Request) -> httpx.Response:
        assert "security_type_desc%3Aeq%3AMarketable" in str(request.url)
        assert "security_class_desc%3Aeq%3ABills" in str(request.url)
        return httpx.Response(
            200,
            request=request,
            json={
                "data": [
                    {
                        "record_date": "2024-01-31",
                        "security_type_desc": "Marketable",
                        "security_class_desc": "Bills",
                        "debt_held_public_mil_amt": "5000000",
                    }
                ]
            },
        )

    provider = TreasuryFiscalDataProvider(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(response)),
    )

    result = provider.fetch_definition(definition)

    assert result.loc[0, "component"] == "marketable_treasury_bills_public"
    assert result.loc[0, "value"] == 5_000_000
