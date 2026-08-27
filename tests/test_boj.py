from datetime import timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.boj import BojError, BojProvider

SERIES_ID = "BS01.MABJMTA"


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="JP",
        group="liquidity",
        name="boj_total_assets",
        classification="measured_data",
        provider="boj",
        series_id=SERIES_ID,
        component="boj_total_assets",
        title="Bank of Japan Accounts: Assets: Total",
        description="Measured test data",
        unit="100 Million Yen",
        frequency="Monthly, End of Period",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2026-01-31").date(),
        source="Bank of Japan",
        source_url="https://www.boj.or.jp/",
    )


def _payload() -> dict[str, object]:
    return {
        "STATUS": 200,
        "MESSAGE": "Successfully completed",
        "RESULTSET": [
            {
                "SERIES_CODE": "MABJMTA",
                "NAME_OF_TIME_SERIES": "Bank of Japan Accounts/Assets/Total",
                "UNIT": "100 million yen",
                "FREQUENCY": "MONTHLY",
                "LAST_UPDATE": 20260805,
                "VALUES": {
                    "SURVEY_DATES": [202601, 202602],
                    "VALUES": [6828680, 6837705],
                },
            }
        ],
    }


def test_fetch_definition_standardizes_exact_monthly_series(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["db"] == "BS01"
        assert request.url.params["code"] == "MABJMTA"
        return httpx.Response(200, json=_payload())

    provider = BojProvider(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.fetch_definition(_definition())

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2026-01-31"), pd.Timestamp("2026-02-28")]
    assert result["value"].tolist() == [6828680, 6837705]
    assert result["country"].unique().tolist() == ["JP"]
    assert result["provider"].unique().tolist() == ["BOJ"]
    assert result["unit"].unique().tolist() == ["100 Million Yen"]


def test_fetch_definition_uses_fresh_cache(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_payload())

    provider = BojProvider(
        cache_dir=tmp_path,
        cache_ttl=timedelta(days=7),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = provider.fetch_definition(_definition())
    second = provider.fetch_definition(_definition())

    assert calls == 1
    pd.testing.assert_frame_equal(first, second)


def test_fetch_definition_rejects_inconsistent_unit_metadata(tmp_path: Path) -> None:
    payload = _payload()
    result_set = payload["RESULTSET"]
    assert isinstance(result_set, list)
    result_set[0]["UNIT"] = "yen"
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
    )
    provider = BojProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BojError, match="does not match the configured unit"):
        provider.fetch_definition(_definition())


def test_fetch_definition_rejects_wrong_series_code(tmp_path: Path) -> None:
    payload = _payload()
    result_set = payload["RESULTSET"]
    assert isinstance(result_set, list)
    result_set[0]["SERIES_CODE"] = "OTHER"
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
    )
    provider = BojProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BojError, match="exact requested code"):
        provider.fetch_definition(_definition())


def test_fetch_definition_reports_http_failure(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(500, text="error"))
    )
    provider = BojProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(BojError, match="HTTP 500"):
        provider.fetch_definition(_definition())
