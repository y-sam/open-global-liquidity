"""Coin Metrics community-data provider for auditable crypto market observations."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
COMMUNITY_API_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
RAW_COLUMNS = ["date", "value", "retrieved_at"]


class CoinMetricsError(RuntimeError):
    """Raised when Coin Metrics community-data ingestion fails."""


class CoinMetricsProvider:
    """Fetch daily Coin Metrics reference rates with a small local Parquet cache.

    Configured series identifiers use ``asset.metric`` notation, for example
    ``btc.PriceUSD``. Community archives are published under CC BY-NC 4.0; callers remain
    responsible for attribution and non-commercial use.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/coinmetrics"),
        timeout_seconds: float = 30.0,
        cache_ttl: timedelta = timedelta(hours=24),
        client: httpx.Client | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.timeout_seconds = timeout_seconds
        self.cache_ttl = cache_ttl
        self._client = client

    def fetch_definition(
        self,
        definition: SeriesDefinition,
        *,
        start: str | date | None = None,
        end: str | date | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Fetch a configured community metric in the project's standardized schema."""
        asset, metric = _parse_series_id(definition.series_id)
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw_observations(asset, metric, force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise CoinMetricsError(
                f"Coin Metrics returned no {definition.series_id} observations in the requested "
                "date range"
            )

        selected["country"] = definition.country
        selected["provider"] = "Coin Metrics"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        standardized = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(standardized)
        return standardized

    def _get_raw_observations(
        self, asset: str, metric: str, *, force_refresh: bool
    ) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{asset}_{metric.lower()}.parquet"
        if not force_refresh and _cache_is_fresh(cache_path, self.cache_ttl):
            cached = pd.read_parquet(cache_path)
            _validate_raw_frame(cached, f"{asset}.{metric}")
            LOGGER.info("Cache hit for %s.%s: %s", asset, metric, cache_path)
            return cached

        LOGGER.info("Cache miss for %s.%s; downloading Coin Metrics community data", asset, metric)
        raw = self._download(asset, metric)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Wrote %d raw observations to %s", len(raw), cache_path)
        return raw

    def _download(self, asset: str, metric: str) -> pd.DataFrame:
        params = {
            "assets": asset,
            "metrics": metric,
            "frequency": "1d",
            "page_size": "10000",
        }
        try:
            if self._client is None:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(COMMUNITY_API_URL, params=params)
            else:
                response = self._client.get(
                    COMMUNITY_API_URL, params=params, timeout=self.timeout_seconds
                )
            response.raise_for_status()
            payload: Any = response.json()
        except httpx.TimeoutException as exc:
            raise CoinMetricsError(
                f"Coin Metrics request for {asset}.{metric} timed out after "
                f"{self.timeout_seconds:g} seconds"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise CoinMetricsError(
                f"Coin Metrics request for {asset}.{metric} failed with HTTP "
                f"{exc.response.status_code}"
            ) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise CoinMetricsError(
                f"Coin Metrics request for {asset}.{metric} failed: {exc}"
            ) from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise CoinMetricsError(
                f"Coin Metrics response for {asset}.{metric} is missing the data collection"
            )
        frame = pd.DataFrame(payload["data"])
        missing = sorted({"time", metric} - set(frame.columns))
        if frame.empty or missing:
            detail = f": {', '.join(missing)}" if missing else ""
            raise CoinMetricsError(
                f"Coin Metrics response for {asset}.{metric} is missing expected data{detail}"
            )
        frame = frame[["time", metric]]
        frame = frame.rename(columns={"time": "date", metric: "value"})
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce", utc=True).dt.tz_localize(
            None
        )
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame["retrieved_at"] = datetime.now(UTC)
        result = frame[RAW_COLUMNS].sort_values("date").reset_index(drop=True)
        _validate_raw_frame(result, f"{asset}.{metric}")
        LOGGER.info(
            "Downloaded %s.%s: %d observations from %s to %s",
            asset,
            metric,
            len(result),
            result["date"].min().date(),
            result["date"].max().date(),
        )
        return result


def _parse_series_id(series_id: str) -> tuple[str, str]:
    parts = series_id.split(".", maxsplit=1)
    if len(parts) != 2 or not all(parts):
        raise CoinMetricsError(
            f"Coin Metrics series_id must use asset.metric notation: {series_id!r}"
        )
    return parts[0].lower(), parts[1]


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc


def _cache_is_fresh(path: Path, ttl: timedelta) -> bool:
    if not path.is_file():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(UTC) - modified <= ttl


def _validate_raw_frame(frame: pd.DataFrame, series_id: str) -> None:
    missing = sorted(set(RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise CoinMetricsError(
            f"Cached Coin Metrics data for {series_id} is missing: {', '.join(missing)}"
        )
    if frame.empty or frame["date"].isna().any() or frame["value"].notna().sum() == 0:
        raise CoinMetricsError(f"Coin Metrics data for {series_id} is empty or invalid")
