from datetime import timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.bis import BisError, BisProvider

SERIES_ID = "BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N"


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="CN",
        group="liquidity",
        name="china_central_bank_total_assets",
        classification="measured_data",
        provider="bis",
        series_id=SERIES_ID,
        component="china_central_bank_total_assets",
        title="China - Central bank, assets, total, BIS-spliced",
        description="Measured test data",
        unit="Billions of Chinese Yuan",
        frequency="Monthly, End of Period",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2025-01-31").date(),
        source="Bank for International Settlements",
        source_url="https://data.bis.org/topics/CBTA",
    )


def _xml(*, key: str = "M.CN.B.XDC.CNY.N", multiplier: str = "9") -> bytes:
    frequency, area, method, unit, currency, transformation = key.split(".")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <message:DataSet>
    <Series FREQ="{frequency}" REF_AREA="{area}" COMP_METHOD="{method}"
      UNIT_MEASURE="{unit}" CURRENCY="{currency}" TRANSFORMATION="{transformation}"
      UNIT_MULT="{multiplier}" TITLE="China - Central bank, assets, total, BIS-spliced">
      <Obs TIME_PERIOD="2025-01" OBS_VALUE="46657.47" OBS_STATUS="A" />
      <Obs TIME_PERIOD="2025-02" OBS_VALUE="47020.53" OBS_STATUS="A" />
    </Series>
  </message:DataSet>
</message:StructureSpecificData>""".encode()


def test_fetch_definition_standardizes_exact_monthly_series(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/BIS/WS_CBTA/1.0/M.CN.B.XDC.CNY.N")
        return httpx.Response(200, content=_xml())

    provider = BisProvider(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.fetch_definition(_definition())

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2025-01-31"), pd.Timestamp("2025-02-28")]
    assert result["value"].tolist() == [46657.47, 47020.53]
    assert result["provider"].unique().tolist() == ["BIS"]
    assert result["unit"].unique().tolist() == ["Billions of Chinese Yuan"]


def test_fetch_definition_uses_fresh_cache(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=_xml())

    provider = BisProvider(
        cache_dir=tmp_path,
        cache_ttl=timedelta(days=7),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = provider.fetch_definition(_definition())
    second = provider.fetch_definition(_definition())

    assert calls == 1
    pd.testing.assert_frame_equal(first, second)


def test_fetch_definition_rejects_wrong_exact_key(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, content=_xml(key="M.US.B.XDC.USD.N"))
        )
    )
    provider = BisProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BisError, match="exact requested key"):
        provider.fetch_definition(_definition())


def test_fetch_definition_rejects_inconsistent_unit_metadata(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, content=_xml(multiplier="6"))
        )
    )
    provider = BisProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BisError, match="does not match monthly CNY billions"):
        provider.fetch_definition(_definition())


def test_fetch_definition_reports_http_failure(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404, text="not found"))
    )
    provider = BisProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BisError, match="HTTP 404"):
        provider.fetch_definition(_definition())
