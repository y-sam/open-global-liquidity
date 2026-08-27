"""Cache-aware provider for official Bank of Japan time-series data."""

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
BOJ_DATA_API_URL = "https://www.stat-search.boj.or.jp/api/v1/getDataCode"
BOJ_RAW_COLUMNS = [
    "date",
    "value",
    "title",
    "unit_code",
    "source_frequency",
    "last_update",
    "retrieved_at",
]


class BojError(RuntimeError):
    """Raised when BOJ data cannot be downloaded or validated safely."""


class BojProvider:
    """Fetch one exact BOJ database/series pair and maintain a Parquet cache.

    BOJ monthly survey periods are represented as calendar month-end dates. This is a period-label
    convention, not an estimate of the public release timestamp. The provider performs no
    interpolation, currency conversion, or cross-country aggregation.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/boj"),
        timeout_seconds: float = 30.0,
        cache_ttl: timedelta = timedelta(days=7),
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
        """Fetch a configured BOJ series in the project's standard long format."""
        if definition.provider.lower() != "boj":
            raise ValueError(f"Expected a BOJ definition, received {definition.provider}")
        database, separator, series_code = definition.series_id.partition(".")
        if not separator or not database or not series_code:
            raise ValueError("BOJ series_id must use the format DATABASE.SERIES_CODE")
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw(database, series_code, force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise BojError(
                f"BOJ returned no {definition.series_id} observations in the requested date range"
            )
        if definition.unit == "100 Million Yen":
            units = set(selected["unit_code"].dropna())
            frequencies = set(selected["source_frequency"].dropna())
            if units != {"100 million yen"} or frequencies != {"MONTHLY"}:
                raise BojError(
                    f"BOJ metadata for {definition.series_id} does not match the configured unit "
                    f"and frequency: units={sorted(units)}, frequencies={sorted(frequencies)}"
                )

        selected["country"] = definition.country
        selected["provider"] = "BOJ"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, database: str, series_code: str, *, force_refresh: bool) -> pd.DataFrame:
        full_id = f"{database}.{series_code}"
        cache_path = self.cache_dir / f"{database.lower()}_{series_code.lower()}.parquet"
        if cache_path.is_file() and not force_refresh:
            age = datetime.now(tz=UTC) - datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            if age <= self.cache_ttl:
                frame = pd.read_parquet(cache_path)
                _validate_raw(frame, full_id)
                LOGGER.info("BOJ cache hit for %s", full_id)
                return frame

        client = self._client or httpx.Client()
        try:
            response = client.get(
                BOJ_DATA_API_URL,
                params={
                    "format": "json",
                    "lang": "en",
                    "db": database,
                    "code": series_code,
                },
                headers={"Accept": "application/json", "User-Agent": "open-global-liquidity/0.2"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise BojError(f"BOJ request for {full_id} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise BojError(
                f"BOJ request for {full_id} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise BojError(f"BOJ request for {full_id} failed: {exc}") from exc
        except ValueError as exc:
            raise BojError(f"BOJ returned invalid JSON for {full_id}") from exc
        finally:
            if self._client is None:
                client.close()

        raw = _parse_payload(payload, full_id, series_code)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Downloaded BOJ %s: %d monthly observations", full_id, len(raw))
        return raw


def _parse_payload(payload: Any, full_id: str, series_code: str) -> pd.DataFrame:
    if not isinstance(payload, dict) or payload.get("STATUS") != 200:
        message = (
            payload.get("MESSAGE", "invalid response")
            if isinstance(payload, dict)
            else "invalid response"
        )
        raise BojError(f"BOJ response for {full_id} failed: {message}")
    result_set = payload.get("RESULTSET")
    if not isinstance(result_set, list) or len(result_set) != 1:
        raise BojError(f"BOJ response for {full_id} must contain exactly one result series")
    result = result_set[0]
    if not isinstance(result, dict) or result.get("SERIES_CODE") != series_code:
        raise BojError(f"BOJ response did not contain the exact requested code {series_code}")
    values_block = result.get("VALUES")
    if not isinstance(values_block, dict):
        raise BojError(f"BOJ response for {full_id} is missing VALUES")
    survey_dates = values_block.get("SURVEY_DATES")
    values = values_block.get("VALUES")
    if not isinstance(survey_dates, list) or not isinstance(values, list):
        raise BojError(f"BOJ response for {full_id} has invalid values arrays")
    if not survey_dates or len(survey_dates) != len(values):
        raise BojError(f"BOJ response for {full_id} has empty or mismatched values arrays")
    periods = pd.to_datetime(
        pd.Series(survey_dates, dtype="string") + "01", format="%Y%m%d", errors="coerce"
    ) + pd.offsets.MonthEnd(0)
    if periods.isna().any():
        raise BojError(f"BOJ returned invalid monthly survey dates for {full_id}")
    raw = pd.DataFrame(
        {
            "date": periods,
            "value": pd.to_numeric(pd.Series(values), errors="coerce"),
            "title": str(result.get("NAME_OF_TIME_SERIES", "")),
            "unit_code": str(result.get("UNIT", "")),
            "source_frequency": str(result.get("FREQUENCY", "")),
            "last_update": str(result.get("LAST_UPDATE", "")),
            "retrieved_at": pd.Timestamp.now(tz=UTC),
        }
    ).sort_values("date", ignore_index=True)
    _validate_raw(raw, full_id)
    return raw


def _validate_raw(frame: pd.DataFrame, full_id: str) -> None:
    missing = sorted(set(BOJ_RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise BojError(f"Cached BOJ data for {full_id} is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise BojError(f"Cached BOJ data for {full_id} is empty")


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc
