from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.boe import BoeError, BoeProvider

SERIES_ID = "RPQB75A"
CSV = "DATE,RPQB75A\n30 Sep 2013,402005\n31 Dec 2013,401181\n"


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="GB",
        group="liquidity",
        name="boe_total_assets",
        classification="measured_data",
        provider="boe",
        series_id=SERIES_ID,
        component="boe_total_assets",
        title="Central Bank Assets: Total",
        description="Measured test data",
        unit="Millions of Sterling",
        frequency="Quarterly",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2013-09-30").date(),
        source="Bank of England",
        source_url="https://www.bankofengland.co.uk/boeapps/database/",
    )


def test_fetch_definition_standardizes_exact_quarterly_series(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["SeriesCodes"] == SERIES_ID
        assert request.url.params["UsingCodes"] == "Y"
        return httpx.Response(200, text=CSV)

    provider = BoeProvider(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.fetch_definition(_definition())

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2013-09-30"), pd.Timestamp("2013-12-31")]
    assert result["value"].tolist() == [402005, 401181]
    assert result["country"].unique().tolist() == ["GB"]
    assert result["provider"].unique().tolist() == ["BOE"]
    assert result["unit"].unique().tolist() == ["Millions of Sterling"]


def test_fetch_definition_uses_fresh_cache(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, text=CSV)

    provider = BoeProvider(
        cache_dir=tmp_path,
        cache_ttl=timedelta(days=7),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = provider.fetch_definition(_definition())
    second = provider.fetch_definition(_definition())

    assert calls == 1
    pd.testing.assert_frame_equal(first, second)


def test_fetch_definition_rejects_unverified_series(tmp_path: Path) -> None:
    provider = BoeProvider(cache_dir=tmp_path)
    unsupported = replace(_definition(), series_id="OTHER")

    with pytest.raises(ValueError, match="supports only"):
        provider.fetch_definition(unsupported)


def test_fetch_definition_rejects_wrong_response_column(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, text="DATE,OTHER\n24 May 2006,1\n")
        )
    )
    provider = BoeProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BoeError, match="missing columns"):
        provider.fetch_definition(_definition())


def test_fetch_definition_reports_http_failure(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(500, text="error"))
    )
    provider = BoeProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BoeError, match="HTTP 500"):
        provider.fetch_definition(_definition())
