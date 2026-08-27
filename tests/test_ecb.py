from datetime import timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.ecb import EcbError, EcbProvider

SERIES_ID = "BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E"


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="EA",
        group="liquidity",
        name="eurosystem_total_assets",
        classification="measured_data",
        provider="ecb",
        series_id=SERIES_ID,
        component="eurosystem_total_assets",
        title="Total assets of the Eurosystem, Stocks",
        description="Measured test data",
        unit="Millions of Euro",
        frequency="Monthly, End of Period",
        seasonal_adjustment="Neither seasonally nor working day adjusted",
        start=pd.Timestamp("2025-01-31").date(),
        source="ECB",
        source_url="https://data.ecb.europa.eu/",
    )


def _csv() -> str:
    return (
        "KEY,TIME_PERIOD,OBS_VALUE,OBS_STATUS,TITLE,UNIT,UNIT_MULT\n"
        f"{SERIES_ID},2025-01,10006342.064171,A,Total assets of the Eurosystem Stocks,EUR,6\n"
        f"{SERIES_ID},2025-02,10088434.000000,A,Total assets of the Eurosystem Stocks,EUR,6\n"
    )


def test_fetch_definition_standardizes_exact_monthly_series(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/BSI/M.U2.N.C.T00.A.1.Z5.0000.Z01.E")
        assert request.url.params["format"] == "csvdata"
        return httpx.Response(200, text=_csv())

    provider = EcbProvider(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.fetch_definition(_definition())

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2025-01-31"), pd.Timestamp("2025-02-28")]
    assert result["value"].tolist() == [10006342.064171, 10088434.0]
    assert result["country"].unique().tolist() == ["EA"]
    assert result["provider"].unique().tolist() == ["ECB"]
    assert result["unit"].unique().tolist() == ["Millions of Euro"]


def test_fetch_definition_uses_fresh_cache(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, text=_csv())

    provider = EcbProvider(
        cache_dir=tmp_path,
        cache_ttl=timedelta(days=7),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = provider.fetch_definition(_definition())
    second = provider.fetch_definition(_definition())

    assert calls == 1
    pd.testing.assert_frame_equal(first, second)


def test_fetch_definition_rejects_inconsistent_unit_metadata(tmp_path: Path) -> None:
    bad_csv = _csv().replace(",EUR,6", ",EUR,9")
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text=bad_csv))
    )
    provider = EcbProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(EcbError, match="does not match Millions of Euro"):
        provider.fetch_definition(_definition())


def test_fetch_definition_reports_missing_columns(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, text="KEY,TIME_PERIOD\nfoo,2025-01\n")
        )
    )
    provider = EcbProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(EcbError, match="missing columns"):
        provider.fetch_definition(_definition())


def test_fetch_definition_reports_http_failure(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404, text="not found"))
    )
    provider = EcbProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(EcbError, match="HTTP 404"):
        provider.fetch_definition(_definition())
