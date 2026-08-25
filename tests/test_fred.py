import logging
from datetime import timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.fred import (
    VINTAGE_COLUMNS,
    FredProvider,
    FredResponseError,
    MissingFredApiKeyError,
)


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="US",
        group="liquidity",
        name="fed_assets",
        classification="measured_data",
        provider="fred",
        series_id="WALCL",
        component="fed_assets",
        title="Fed assets",
        description="Test series",
        unit="Millions of U.S. Dollars",
        frequency="Weekly, As of Wednesday",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2024-01-01").date(),
        source="Federal Reserve",
        source_url="https://fred.stlouisfed.org/series/WALCL",
    )


def _response(request: httpx.Request) -> httpx.Response:
    assert request.url.params["series_id"] == "WALCL"
    assert request.url.params["observation_start"] == "2024-01-01"
    return httpx.Response(
        200,
        request=request,
        json={
            "observations": [
                {
                    "realtime_start": "2024-01-11",
                    "realtime_end": "2024-01-11",
                    "date": "2024-01-03",
                    "value": "6794581",
                },
                {
                    "realtime_start": "2024-01-11",
                    "realtime_end": "2024-01-11",
                    "date": "2024-01-10",
                    "value": ".",
                },
            ]
        },
    )


def test_fetch_standardizes_and_caches_observations(tmp_path: Path) -> None:
    client = httpx.Client(transport=httpx.MockTransport(_response))
    provider = FredProvider(api_key="test-key", cache_dir=tmp_path, client=client)

    result = provider.fetch(
        "WALCL",
        "2024-01-01",
        component="fed_assets",
        unit="Millions of U.S. Dollars",
        frequency="Weekly, As of Wednesday",
    )

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-10")]
    assert result.loc[0, "value"] == 6_794_581
    assert pd.isna(result.loc[1, "value"])
    assert result["provider"].unique().tolist() == ["FRED"]
    assert (tmp_path / "WALCL.parquet").is_file()


def test_fresh_cache_avoids_network(tmp_path: Path) -> None:
    raw = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03"]),
            "value": [6_794_581.0],
            "realtime_start": ["2024-01-11"],
            "realtime_end": ["2024-01-11"],
            "retrieved_at": [pd.Timestamp("2024-01-11", tz="UTC")],
        }
    )
    raw.to_parquet(tmp_path / "WALCL.parquet", index=False)

    def fail_on_request(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("fresh cache should prevent network access")

    provider = FredProvider(
        api_key="test-key",
        cache_dir=tmp_path,
        cache_ttl=timedelta(days=1),
        client=httpx.Client(transport=httpx.MockTransport(fail_on_request)),
    )

    result = provider.fetch("WALCL", "2024-01-01")

    assert len(result) == 1
    assert result.loc[0, "value"] == 6_794_581


def test_missing_api_key_fails_clearly(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(MissingFredApiKeyError, match="FRED_API_KEY is missing"):
        FredProvider(cache_dir=tmp_path)


def test_provider_suppresses_request_url_logging(tmp_path: Path) -> None:
    httpx_logger = logging.getLogger("httpx")
    previous_level = httpx_logger.level
    httpx_logger.setLevel(logging.INFO)
    try:
        FredProvider(api_key="test-key", cache_dir=tmp_path)
        assert httpx_logger.level == logging.WARNING
    finally:
        httpx_logger.setLevel(previous_level)


def test_invalid_response_schema_fails_clearly(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, request=request, json={}))
    )
    provider = FredProvider(api_key="test-key", cache_dir=tmp_path, client=client)

    with pytest.raises(FredResponseError, match="missing the observations collection"):
        provider.fetch("WALCL", "2024-01-01")


def test_fetch_vintage_dates_uses_alfred_release_history(tmp_path: Path) -> None:
    def response(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/fred/series/vintagedates")
        assert request.url.params["realtime_start"] == "2024-01-01"
        return httpx.Response(
            200,
            request=request,
            json={"vintage_dates": ["2024-01-04", "2024-01-11"]},
        )

    provider = FredProvider(
        api_key="test-key",
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(response)),
    )

    result = provider.fetch_vintage_dates("WALCL", start="2024-01-01")

    assert result["provider"].unique().tolist() == ["ALFRED"]
    assert result["vintage_date"].tolist() == [
        pd.Timestamp("2024-01-04"),
        pd.Timestamp("2024-01-11"),
    ]


def test_fetch_vintage_definition_preserves_as_of_lineage_and_cache(tmp_path: Path) -> None:
    requests = 0

    def response(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert request.url.params["vintage_dates"] == "2024-01-11"
        assert request.url.params["output_type"] == "1"
        return httpx.Response(
            200,
            request=request,
            json={
                "observations": [
                    {
                        "realtime_start": "2024-01-11",
                        "realtime_end": "9999-12-31",
                        "date": "2024-01-03",
                        "value": "6794581",
                    }
                ]
            },
        )

    provider = FredProvider(
        api_key="test-key",
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(response)),
    )
    first = provider.fetch_vintage_definition(_definition(), vintage_date="2024-01-11")
    second = provider.fetch_vintage_definition(_definition(), vintage_date="2024-01-11")

    assert first.columns.tolist() == VINTAGE_COLUMNS
    assert first["provider"].unique().tolist() == ["ALFRED"]
    assert first["vintage_date"].item() == pd.Timestamp("2024-01-11")
    assert first["observation_date"].item() == pd.Timestamp("2024-01-03")
    assert first["value"].item() == 6_794_581
    pd.testing.assert_frame_equal(first, second)
    assert requests == 1


def test_fetch_vintage_batch_converts_alfred_crosstab_to_long_contract(tmp_path: Path) -> None:
    requests = 0

    def response(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert request.url.params["output_type"] == "2"
        assert request.url.params["vintage_dates"] == "2024-01-05,2024-01-12"
        return httpx.Response(
            200,
            request=request,
            json={
                "observations": [
                    {
                        "date": "2024-01-03",
                        "WALCL_20240105": "100.0",
                        "WALCL_20240112": "101.0",
                    },
                    {
                        "date": "2024-01-10",
                        "WALCL_20240105": ".",
                        "WALCL_20240112": "102.0",
                    },
                ]
            },
        )

    provider = FredProvider(
        api_key="test-key",
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(response)),
    )
    first = provider.fetch_vintage_batch_definition(
        _definition(), vintage_dates=["2024-01-12", "2024-01-05"]
    )
    second = provider.fetch_vintage_batch_definition(
        _definition(), vintage_dates=["2024-01-05", "2024-01-12"]
    )

    assert first.columns.tolist() == VINTAGE_COLUMNS
    assert first.groupby("vintage_date").size().to_dict() == {
        pd.Timestamp("2024-01-05"): 1,
        pd.Timestamp("2024-01-12"): 2,
    }
    assert first["value"].tolist() == [100.0, 101.0, 102.0]
    assert first["realtime_start"].isna().all()
    pd.testing.assert_frame_equal(first, second)
    assert requests == 1
