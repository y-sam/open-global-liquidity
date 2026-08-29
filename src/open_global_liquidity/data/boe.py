"""Cache-aware provider for official Bank of England database observations."""

from __future__ import annotations

import io
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
BOE_DATABASE_URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"
BOE_TOTAL_ASSETS_SERIES = "RPQB75A"
BOE_RAW_COLUMNS = ["date", "value", "source_column", "retrieved_at"]


class BoeError(RuntimeError):
    """Raised when Bank of England data cannot be downloaded or validated safely."""


class BoeProvider:
    """Fetch exact BoE database series and maintain a small local Parquet cache.

    The v0.2 pilot deliberately supports the verified ``RPQB75A`` quarterly central-bank
    total-assets
    series only. Source observation dates are preserved as published. The provider performs no
    interpolation, currency conversion, or cross-country aggregation.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/boe"),
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
        """Fetch the configured BoE total-assets series in standard long format."""
        if definition.provider.lower() != "boe":
            raise ValueError(f"Expected a BoE definition, received {definition.provider}")
        if definition.series_id != BOE_TOTAL_ASSETS_SERIES:
            raise ValueError(
                f"BoE pilot supports only the verified {BOE_TOTAL_ASSETS_SERIES} series"
            )
        if definition.unit != "Millions of Sterling" or definition.frequency != "Quarterly":
            raise BoeError(
                f"BoE configuration for {definition.series_id} must use Millions of Sterling "
                "and Quarterly frequency"
            )
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw(definition.series_id, force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise BoeError(
                f"BoE returned no {definition.series_id} observations in the requested date range"
            )

        selected["country"] = definition.country
        selected["provider"] = "BOE"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, series_id: str, *, force_refresh: bool) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{series_id.lower()}.parquet"
        if cache_path.is_file() and not force_refresh:
            age = datetime.now(tz=UTC) - datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            if age <= self.cache_ttl:
                frame = pd.read_parquet(cache_path)
                _validate_raw(frame, series_id)
                LOGGER.info("BoE cache hit for %s", series_id)
                return frame

        client = self._client or httpx.Client()
        try:
            response = client.get(
                BOE_DATABASE_URL,
                params={
                    "csv.x": "yes",
                    "Datefrom": "01/Jan/2013",
                    "Dateto": "now",
                    "SeriesCodes": series_id,
                    "CSVF": "TN",
                    "UsingCodes": "Y",
                    "VPD": "Y",
                    "VFD": "N",
                },
                headers={"Accept": "text/csv", "User-Agent": "open-global-liquidity/0.2"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise BoeError(f"BoE request for {series_id} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise BoeError(
                f"BoE request for {series_id} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise BoeError(f"BoE request for {series_id} failed: {exc}") from exc
        finally:
            if self._client is None:
                client.close()

        raw = _parse_csv(response.text, series_id)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Downloaded BoE %s: %d quarterly observations", series_id, len(raw))
        return raw


def _parse_csv(text: str, series_id: str) -> pd.DataFrame:
    try:
        source = pd.read_csv(io.StringIO(text))
    except (pd.errors.ParserError, UnicodeError) as exc:
        raise BoeError(f"BoE returned invalid CSV for {series_id}") from exc
    expected = {"DATE", series_id}
    missing = sorted(expected - set(source.columns))
    if missing:
        raise BoeError(f"BoE response for {series_id} is missing columns: {', '.join(missing)}")
    unexpected_series = sorted(
        column for column in source.columns if column != "DATE" and column != series_id
    )
    if unexpected_series:
        raise BoeError(
            f"BoE response for {series_id} included unexpected series columns: "
            f"{', '.join(unexpected_series)}"
        )
    if source.empty:
        raise BoeError(f"BoE returned no observations for {series_id}")
    dates = pd.to_datetime(source["DATE"], format="%d %b %Y", errors="coerce")
    if dates.isna().any():
        raise BoeError(f"BoE returned invalid observation dates for {series_id}")
    raw = pd.DataFrame(
        {
            "date": dates,
            "value": pd.to_numeric(source[series_id], errors="coerce"),
            "source_column": series_id,
            "retrieved_at": pd.Timestamp.now(tz=UTC),
        }
    ).sort_values("date", ignore_index=True)
    _validate_raw(raw, series_id)
    return raw


def _validate_raw(frame: pd.DataFrame, series_id: str) -> None:
    missing = sorted(set(BOE_RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise BoeError(f"Cached BoE data for {series_id} is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise BoeError(f"Cached BoE data for {series_id} is empty")
    if set(frame["source_column"].dropna()) != {series_id}:
        raise BoeError(f"Cached BoE data does not contain the exact requested series {series_id}")


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc
