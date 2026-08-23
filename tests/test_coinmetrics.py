from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.coinmetrics import CoinMetricsError, CoinMetricsProvider


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="US",
        group="markets",
        name="bitcoin",
        classification="measured_data",
        provider="coinmetrics",
        series_id="btc.PriceUSD",
        component="bitcoin",
        title="Bitcoin reference rate",
        description="Test data",
        unit="U.S. Dollars per Bitcoin",
        frequency="Daily",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=pd.Timestamp("2024-01-01").date(),
        source="Coin Metrics Community Data",
        source_url="https://community-api.coinmetrics.io/v4/",
    )


def test_fetch_standardizes_coinmetrics_reference_rate(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                request=request,
                json={
                    "data": [
                        {"asset": "btc", "time": "2024-01-01T00:00:00Z", "PriceUSD": "42000"},
                        {"asset": "btc", "time": "2024-01-02T00:00:00Z", "PriceUSD": "43000"},
                    ]
                },
            )
        )
    )
    provider = CoinMetricsProvider(cache_dir=tmp_path, client=client)

    result = provider.fetch_definition(_definition(), start="2024-01-02")

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result["date"].tolist() == [pd.Timestamp("2024-01-02")]
    assert result["value"].tolist() == [43_000]
    assert result["provider"].unique().tolist() == ["Coin Metrics"]
    assert (tmp_path / "btc_priceusd.parquet").is_file()


def test_missing_metric_fails_clearly(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, request=request, json={"data": []})
        )
    )
    provider = CoinMetricsProvider(cache_dir=tmp_path, client=client)

    with pytest.raises(CoinMetricsError, match="missing expected data"):
        provider.fetch_definition(_definition())
