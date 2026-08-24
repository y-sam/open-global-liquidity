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
FRED_VINTAGE_DATES_URL = "https://api.stlouisfed.org/fred/series/vintagedates"
RAW_COLUMNS = ["date", "value", "realtime_start", "realtime_end", "retrieved_at"]
VINTAGE_COLUMNS = [
    "observation_date",
    "vintage_date",
    "country",
    "provider",
    "series_id",
    "component",
    "value",
    "unit",
    "frequency",
    "realtime_start",
    "realtime_end",
    "retrieved_at",
]


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

    def fetch_vintage_dates(
        self,
        series_id: str,
        *,
        start: str | date | None = None,
        end: str | date | None = None,
    ) -> pd.DataFrame:
        """Return ALFRED dates when a series first appeared or changed.

        A vintage date records a release or revision event in ALFRED. It is not necessarily the
        same as an observation date or the originating agency's announced release timestamp.
        """
        start_date = _coerce_date(start, "start") if start is not None else None
        end_date = _coerce_date(end, "end") if end is not None else None
        if start_date is not None and end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")
        params: dict[str, str] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "asc",
            "limit": "10000",
        }
        if start_date is not None:
            params["realtime_start"] = start_date.isoformat()
        if end_date is not None:
            params["realtime_end"] = end_date.isoformat()
        payload = self._request_json(
            FRED_VINTAGE_DATES_URL,
            params=params,
            request_label=f"FRED vintage-date request for {series_id}",
        )
        values = payload.get("vintage_dates") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise FredResponseError(
                f"FRED vintage-date response for {series_id} is missing vintage_dates"
            )
        dates = pd.to_datetime(pd.Series(values, dtype="string"), errors="coerce")
        if dates.isna().any():
            raise FredResponseError(f"FRED returned invalid vintage dates for {series_id}")
        return pd.DataFrame(
            {
                "provider": "ALFRED",
                "series_id": series_id,
                "vintage_date": dates,
                "retrieved_at": pd.Timestamp.now(tz=UTC),
            }
        )

    def fetch_vintage_definition(
        self,
        definition: SeriesDefinition,
        *,
        vintage_date: str | date,
        start: str | date | None = None,
        end: str | date | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Fetch a configured FRED series exactly as ALFRED reports it on an as-of date."""
        as_of = _coerce_date(vintage_date, "vintage_date")
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if as_of < start_date:
            raise ValueError("vintage_date cannot precede the requested observation start")
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")
        cache_path = self.cache_dir / "vintages" / definition.series_id / f"{as_of}.parquet"
        if cache_path.is_file() and not force_refresh:
            frame = pd.read_parquet(cache_path)
            _validate_vintage_frame(frame, definition.series_id, as_of)
            LOGGER.info("Vintage cache hit for %s as of %s", definition.series_id, as_of)
            return frame

        params: dict[str, str] = {
            "series_id": definition.series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date.isoformat(),
            "vintage_dates": as_of.isoformat(),
            "output_type": "1",
            "sort_order": "asc",
        }
        if end_date is not None:
            params["observation_end"] = end_date.isoformat()
        payload = self._request_json(
            FRED_OBSERVATIONS_URL,
            params=params,
            request_label=f"ALFRED as-of request for {definition.series_id} on {as_of}",
        )
        observations = payload.get("observations") if isinstance(payload, dict) else None
        if not isinstance(observations, list):
            raise FredResponseError(
                f"ALFRED response for {definition.series_id} is missing observations"
            )
        if not observations:
            raise FredResponseError(
                f"ALFRED returned no {definition.series_id} observations as of {as_of}"
            )
        raw = pd.DataFrame(observations)
        required = {"date", "value", "realtime_start", "realtime_end"}
        missing = sorted(required - set(raw.columns))
        if missing:
            raise FredResponseError(
                f"ALFRED response for {definition.series_id} is missing: {', '.join(missing)}"
            )
        frame = (
            pd.DataFrame(
                {
                    "observation_date": pd.to_datetime(raw["date"], errors="coerce"),
                    "vintage_date": pd.Timestamp(as_of),
                    "country": definition.country,
                    "provider": "ALFRED",
                    "series_id": definition.series_id,
                    "component": definition.component,
                    "value": pd.to_numeric(raw["value"].replace(".", pd.NA), errors="coerce"),
                    "unit": definition.unit,
                    "frequency": definition.frequency,
                    "realtime_start": raw["realtime_start"].astype("string"),
                    "realtime_end": raw["realtime_end"].astype("string"),
                    "retrieved_at": pd.Timestamp.now(tz=UTC),
                }
            )[VINTAGE_COLUMNS]
            .sort_values("observation_date")
            .reset_index(drop=True)
        )
        frame["observation_date"] = frame["observation_date"].astype("datetime64[ns]")
        frame["vintage_date"] = frame["vintage_date"].astype("datetime64[ns]")
        _validate_vintage_frame(frame, definition.series_id, as_of)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(cache_path, index=False)
        LOGGER.info(
            "Wrote %d %s vintage observations as of %s to %s",
            len(frame),
            definition.series_id,
            as_of,
            cache_path,
        )
        return frame

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

        payload = self._request_json(
            FRED_OBSERVATIONS_URL,
            params=params,
            request_label=f"FRED request for {series_id}",
        )

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

    def _request_json(
        self,
        url: str,
        *,
        params: dict[str, str],
        request_label: str,
    ) -> Any:
        """Execute one authenticated FRED/ALFRED request with consistent failures."""
        try:
            if self._client is None:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(url, params=params)
            else:
                response = self._client.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise FredResponseError(
                f"{request_label} timed out after {self.timeout_seconds:g} seconds"
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = _fred_error_detail(exc.response)
            raise FredResponseError(
                f"{request_label} failed with HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise FredResponseError(f"{request_label} failed: {exc}") from exc


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


def _validate_vintage_frame(frame: pd.DataFrame, series_id: str, vintage_date: date) -> None:
    missing = [column for column in VINTAGE_COLUMNS if column not in frame.columns]
    if missing:
        raise FredResponseError(
            f"Cached ALFRED data for {series_id} is missing: {', '.join(missing)}"
        )
    if frame.empty or frame["value"].notna().sum() == 0:
        raise FredResponseError(f"Cached ALFRED data for {series_id} as of {vintage_date} is empty")
    if frame["observation_date"].isna().any():
        raise FredResponseError(f"Cached ALFRED data for {series_id} has invalid observations")
    if not frame["vintage_date"].eq(pd.Timestamp(vintage_date)).all():
        raise FredResponseError(f"Cached ALFRED data for {series_id} has the wrong vintage date")


def _fred_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200] or "no response body"
    if isinstance(payload, dict):
        return str(payload.get("error_message") or payload.get("message") or payload)[:200]
    return str(payload)[:200]
