"""Cache-aware provider for measured ECB Data Portal observations."""

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
ECB_DATA_API_URL = "https://data-api.ecb.europa.eu/service/data"
ECB_RAW_COLUMNS = [
    "date",
    "value",
    "obs_status",
    "title",
    "unit_code",
    "unit_multiplier",
    "retrieved_at",
]


class EcbError(RuntimeError):
    """Raised when ECB data cannot be downloaded or validated safely."""


class EcbProvider:
    """Fetch exact ECB series keys and maintain a small local Parquet cache.

    Monthly ECB periods are represented as calendar month-end dates. This is a period-label
    convention only; it does not claim that the observation was publicly available on that date.
    No interpolation or frequency conversion is performed by this provider.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/ecb"),
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
        """Fetch one configured, fully qualified ECB series in standard long format."""
        if definition.provider.lower() != "ecb":
            raise ValueError(f"Expected an ECB definition, received {definition.provider}")
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
            raise EcbError(
                f"ECB returned no {definition.series_id} observations in the requested date range"
            )
        if definition.unit == "Millions of Euro":
            unit_pairs = set(zip(selected["unit_code"], selected["unit_multiplier"], strict=True))
            if unit_pairs != {("EUR", 6)}:
                raise EcbError(
                    f"ECB metadata for {definition.series_id} does not match Millions of Euro: "
                    f"{sorted(unit_pairs)}"
                )

        selected["country"] = definition.country
        selected["provider"] = "ECB"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, series_id: str, *, force_refresh: bool) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{series_id.lower().replace('.', '_')}.parquet"
        if cache_path.is_file() and not force_refresh:
            age = datetime.now(tz=UTC) - datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            if age <= self.cache_ttl:
                frame = pd.read_parquet(cache_path)
                _validate_raw(frame, series_id)
                LOGGER.info("ECB cache hit for %s", series_id)
                return frame

        flow, separator, key = series_id.partition(".")
        if not separator or not flow or not key:
            raise ValueError("ECB series_id must contain a dataflow and exact series key")
        client = self._client or httpx.Client()
        try:
            response = client.get(
                f"{ECB_DATA_API_URL}/{flow}/{key}",
                params={"format": "csvdata"},
                headers={"Accept": "text/csv", "User-Agent": "open-global-liquidity/0.2"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise EcbError(f"ECB request for {series_id} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise EcbError(
                f"ECB request for {series_id} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise EcbError(f"ECB request for {series_id} failed: {exc}") from exc
        finally:
            if self._client is None:
                client.close()

        try:
            source = pd.read_csv(io.StringIO(response.text))
        except (pd.errors.ParserError, UnicodeError) as exc:
            raise EcbError(f"ECB returned invalid CSV for {series_id}") from exc
        required = {"KEY", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "TITLE", "UNIT", "UNIT_MULT"}
        missing = sorted(required - set(source.columns))
        if missing:
            raise EcbError(f"ECB response for {series_id} is missing columns: {', '.join(missing)}")
        if source.empty:
            raise EcbError(f"ECB returned no observations for {series_id}")
        keys = set(source["KEY"].dropna().astype(str))
        if keys != {series_id}:
            raise EcbError(f"ECB response did not contain the exact requested key {series_id}")

        periods = pd.to_datetime(
            source["TIME_PERIOD"].astype("string") + "-01", errors="coerce"
        ) + pd.offsets.MonthEnd(0)
        if periods.isna().any():
            raise EcbError(f"ECB returned invalid monthly periods for {series_id}")
        retrieved_at = pd.Timestamp.now(tz=UTC)
        raw = pd.DataFrame(
            {
                "date": periods,
                "value": pd.to_numeric(source["OBS_VALUE"], errors="coerce"),
                "obs_status": source["OBS_STATUS"].astype("string"),
                "title": source["TITLE"].astype("string"),
                "unit_code": source["UNIT"].astype("string"),
                "unit_multiplier": pd.to_numeric(source["UNIT_MULT"], errors="coerce"),
                "retrieved_at": retrieved_at,
            }
        ).sort_values("date", ignore_index=True)
        _validate_raw(raw, series_id)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Downloaded ECB %s: %d monthly observations", series_id, len(raw))
        return raw


def _validate_raw(frame: pd.DataFrame, series_id: str) -> None:
    missing = sorted(set(ECB_RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise EcbError(f"Cached ECB data for {series_id} is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise EcbError(f"Cached ECB data for {series_id} is empty")


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc
