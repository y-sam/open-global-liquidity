"""Minimal, cache-aware FRED observations provider."""

from __future__ import annotations

import logging
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
RAW_COLUMNS = ["date", "value", "realtime_start", "realtime_end", "retrieved_at"]


class FredError(RuntimeError):
    """Base exception for a FRED ingestion failure."""


class MissingFredApiKeyError(FredError):
    """Raised when no FRED API key is available."""


class FredResponseError(FredError):
    """Raised when FRED is unavailable or returns unusable data."""


class FredProvider:
    """Fetch current-vintage FRED observations and maintain a small Parquet cache.

    Missing FRED values use the provider's ``.`` marker. They are retained as ``NaN`` so
    downstream code can apply an explicit economic-series policy instead of silently interpolating
    or discarding observations.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        cache_dir: Path = Path("data/raw/fred"),
        timeout_seconds: float = 30.0,
        cache_ttl: timedelta = timedelta(hours=24),
        client: httpx.Client | None = None,
    ) -> None:
        # FRED v1 places credentials in the query string, which httpx includes in INFO request logs.
        # Suppress transport request logging for every provider use, including notebooks.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise MissingFredApiKeyError(
                "FRED_API_KEY is missing. Copy .env.example to .env and add a FRED API key."
            )
        self.cache_dir = cache_dir
        self.timeout_seconds = timeout_seconds
        self.cache_ttl = cache_ttl
        self._client = client

    def fetch(
        self,
        series_id: str,
        start: str | date,
        end: str | date | None = None,
        *,
        country: str = "US",
        component: str | None = None,
        unit: str = "Unknown",
        frequency: str = "Unknown",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Return one series in the project's deterministic long-format column order."""
        start_date = _coerce_date(start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw_observations(
            series_id=series_id,
            start=start_date,
            end=end_date,
            force_refresh=force_refresh,
        )
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        if selected.empty:
            raise FredResponseError(
                f"FRED returned no {series_id} observations in the requested date range"
            )

        selected["country"] = country
        selected["provider"] = "FRED"
        selected["series_id"] = series_id
        selected["component"] = component or series_id.lower()
        selected["unit"] = unit
        selected["frequency"] = frequency
        standardized = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(standardized)
        return standardized

    def fetch_definition(
        self,
        definition: SeriesDefinition,
        *,
        start: str | date | None = None,
        end: str | date | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Fetch a configured measured series without duplicating its metadata in code."""
        return self.fetch(
            series_id=definition.series_id,
            start=start or definition.start,
            end=end,
            country=definition.country,
            component=definition.component,
            unit=definition.unit,
            frequency=definition.frequency,
            force_refresh=force_refresh,
        )

    def _get_raw_observations(
        self,
        *,
        series_id: str,
        start: date,
        end: date | None,
        force_refresh: bool,
    ) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{series_id}.parquet"
        if not force_refresh and _cache_is_fresh(cache_path, self.cache_ttl):
            cached = pd.read_parquet(cache_path)
            _validate_raw_frame(cached, series_id)
            observation_tolerance = timedelta(days=7)
            cache_starts_early_enough = cached["date"].min().date() <= start + observation_tolerance
            cache_ends_late_enough = (
                end is None or cached["date"].max().date() >= end - observation_tolerance
            )
            if cache_starts_early_enough and cache_ends_late_enough:
                LOGGER.info("Cache hit for %s: %s", series_id, cache_path)
                return cached
            LOGGER.info("Cache does not cover requested range for %s; refreshing", series_id)

        LOGGER.info("Cache miss for %s; downloading from FRED", series_id)
        raw = self._download(series_id=series_id, start=start, end=end)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Wrote %d raw observations to %s", len(raw), cache_path)
        return raw

    def _download(self, *, series_id: str, start: date, end: date | None) -> pd.DataFrame:
        params: dict[str, str] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start.isoformat(),
            "sort_order": "asc",
        }
        if end is not None:
            params["observation_end"] = end.isoformat()

        try:
            if self._client is None:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(FRED_OBSERVATIONS_URL, params=params)
            else:
                response = self._client.get(
                    FRED_OBSERVATIONS_URL, params=params, timeout=self.timeout_seconds
                )
            response.raise_for_status()
            payload: Any = response.json()
        except httpx.TimeoutException as exc:
            raise FredResponseError(
                f"FRED request for {series_id} timed out after {self.timeout_seconds:g} seconds"
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = _fred_error_detail(exc.response)
            raise FredResponseError(
                f"FRED request for {series_id} failed with HTTP "
                f"{exc.response.status_code}: {detail}"
            ) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise FredResponseError(f"FRED request for {series_id} failed: {exc}") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("observations"), list):
            raise FredResponseError(
                f"FRED response for {series_id} is missing the observations collection"
            )
        observations = payload["observations"]
        if not observations:
            raise FredResponseError(f"FRED returned no observations for {series_id}")

        frame = pd.DataFrame(observations)
        required = {"date", "value", "realtime_start", "realtime_end"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise FredResponseError(
                f"FRED response for {series_id} is missing columns: {', '.join(missing)}"
            )

        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        if frame["date"].isna().any():
            raise FredResponseError(f"FRED response for {series_id} contains invalid dates")
        frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
        retrieved_at = datetime.now(UTC)
        frame["retrieved_at"] = retrieved_at
        result = frame[RAW_COLUMNS].sort_values("date").reset_index(drop=True)
        _validate_raw_frame(result, series_id)
        LOGGER.info(
            "Downloaded %s: %d observations from %s to %s",
            series_id,
            len(result),
            result["date"].min().date(),
            result["date"].max().date(),
        )
        return result


def _coerce_date(value: str | date, field: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date (YYYY-MM-DD), got {value!r}") from exc


def _cache_is_fresh(path: Path, ttl: timedelta) -> bool:
    if not path.is_file():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(UTC) - modified <= ttl


def _validate_raw_frame(frame: pd.DataFrame, series_id: str) -> None:
    missing = [column for column in RAW_COLUMNS if column not in frame.columns]
    if missing:
        raise FredResponseError(
            f"Cached FRED data for {series_id} is missing columns: {', '.join(missing)}"
        )
    if frame.empty:
        raise FredResponseError(f"Cached FRED data for {series_id} is empty")


def _fred_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200] or "no response body"
    if isinstance(payload, dict):
        return str(payload.get("error_message") or payload.get("message") or payload)[:200]
    return str(payload)[:200]
